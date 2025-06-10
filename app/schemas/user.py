from pydantic import BaseModel, EmailStr

class ProfileOut(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
