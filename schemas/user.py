import uuid
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    pass

# Properties stored in DB
class UserInDB(UserBase):
    id: uuid.UUID
    hashed_password: str

    class Config:
        from_attributes = True

# Properties to return to client
class User(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True