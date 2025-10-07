import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

# Properties for changing password
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# Properties stored in DB
class UserInDB(UserBase):
    id: uuid.UUID
    password_hash: str

    class Config:
        from_attributes = True

# Properties to return to client
class User(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
