from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class VerifyIn(BaseModel):
    email: EmailStr
    code: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    code: str
    new_password: str

class ChangePasswordIn(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    new_password2: str = Field(..., min_length=6)