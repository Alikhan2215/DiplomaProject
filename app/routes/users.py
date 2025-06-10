from fastapi import APIRouter, Depends, HTTPException, Header
from app.schemas.user import ProfileOut, ProfileUpdate
from app.core.security import get_current_user
from app.core.db import db

router = APIRouter()

@router.get("/me", response_model=ProfileOut)
async def read_profile(current_user=Depends(get_current_user)):
    return ProfileOut(
        email=current_user["email"],
        first_name=current_user.get("first_name", "User"),
        last_name=current_user.get("last_name", "User"),
    )

@router.put("/me", response_model=ProfileOut)
async def update_profile(
    data: ProfileUpdate,
    current_user=Depends(get_current_user),
):
    await db.users.update_one(
        {"email": current_user["email"]},
        {"$set": {"first_name": data.first_name, "last_name": data.last_name}}
    )
    user = await db.users.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ProfileOut(
        email=user["email"],
        first_name=user.get("first_name", "User"),
        last_name=user.get("last_name", "User"),
    )
