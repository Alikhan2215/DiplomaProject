from fastapi import APIRouter, HTTPException, status, Response, Depends
from datetime import datetime, timedelta
import random
from app.schemas.auth import RegisterIn, VerifyIn, LoginIn, TokenOut, ChangePasswordIn, ForgotPasswordIn, ResetPasswordIn
from app.utils.email_utils import send_verification_email
from app.core.security import get_current_user, get_password_hash, create_access_token, verify_password
from app.core.config import settings
from app.core.db import db
from app.services.reset_service import create_reset_code, consume_reset_code
router = APIRouter()

verification_store: dict[str, dict] = {}
CODE_EXPIRY_MINUTES = 30

@router.post("/register", status_code=201)
async def register(data: RegisterIn):
    # 1) check if user exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2) hash password
    hashed = get_password_hash(data.password)

    # 3) generate 6-digit code
    code = f"{random.randint(0, 999999):06d}"
    expire_at = datetime.utcnow() + timedelta(minutes=CODE_EXPIRY_MINUTES)
    # temporarily store
    verification_store[data.email] = {"code": code, "expires": expire_at, "hashed_password": hashed}

    # 4) send email
    send_verification_email(data.email, code)

    return {"msg": "Verification code sent"}

@router.post("/verify")
async def verify(data: VerifyIn):
    record = verification_store.get(data.email)
    if not record or record["code"] != data.code:
        raise HTTPException(status_code=400, detail="Invalid code")
    if datetime.utcnow() > record["expires"]:
        verification_store.pop(data.email, None)
        raise HTTPException(status_code=400, detail="Code expired")

    # insert into DB
    await db.users.insert_one({
        "email": data.email,
        "hashed_password": record["hashed_password"],
        "is_verified": True,
        "first_name": "User",
        "last_name": "User"
    })
    # clean up
    verification_store.pop(data.email, None)
    return {"msg": "Email verified, registration complete"}

@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn):
    user = await db.users.find_one({"email": data.email})
    if not user or not user.get("is_verified", False):
        raise HTTPException(status_code=400, detail="Invalid credentials or unverified")
    if not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(subject=user["email"])
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    For bearer‐token auth, logout is purely client‐side (drop the token).
    This endpoint exists so the front‐end can call it and react.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordIn):
    user = await db.users.find_one({"email": data.email})
    if not user:
        # To avoid leaking which emails exist, you can still return 200
        raise HTTPException(status_code=404, detail="No such user")

    code = await create_reset_code(data.email)
    send_verification_email(data.email, code)
    return {"msg": "Reset code sent"}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordIn):
    """
    Expects JSON:
      {
        "code": "123456",
        "new_password": "MyNewSecret"
      }
    """
    email = await consume_reset_code(data.code)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    hashed = get_password_hash(data.new_password)
    await db.users.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed}}
    )
    return {"msg": "Password has been reset"}

@router.post("/change-password")
async def change_password(
    data: ChangePasswordIn,
    user=Depends(get_current_user)
):
    """
    Change password when logged in: supply old, new, new again.
    """
    # 1) Check the two new passwords match
    if data.new_password != data.new_password2:
        raise HTTPException(
            status_code=400,
            detail="New passwords do not match."
        )

    # 2) Verify old password is correct
    if not verify_password(data.old_password, user["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Old password is incorrect."
        )

    # 3) Hash & persist the new password
    new_hashed = get_password_hash(data.new_password)
    await db.users.update_one(
        {"email": user["email"]},
        {"$set": {"hashed_password": new_hashed}}
    )

    return {"msg": "Password changed successfully."}