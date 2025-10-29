import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(BaseModel):
    full_name: Optional[str] = None

# Properties for updating password
class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# Properties for an admin to update a user
class UserAdminUpdate(BaseModel):
    is_superuser: Optional[bool] = None

# Properties stored in DB
class UserInDB(UserBase):
    id: uuid.UUID
    is_superuser: bool
    password_hash: str

    class Config:
        from_attributes = True

# Properties to return to client
class User(UserBase):
    id: uuid.UUID
    is_superuser: bool

    class Config:
        from_attributes = True

