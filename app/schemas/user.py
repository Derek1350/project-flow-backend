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
    # --- ADDED NOTIFICATION FIELDS ---
    notify_on_assignment: Optional[bool] = None
    notify_on_proposal: Optional[bool] = None

# Properties for updating password
class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# Properties for an admin to update a user's role
class UserAdminUpdate(BaseModel):
    is_superuser: Optional[bool] = None

# Properties for an admin to fully update a user
class UserAdminFullUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None # Admin can optionally reset a password

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
    # --- ADDED NOTIFICATION FIELDS ---
    notify_on_assignment: bool
    notify_on_proposal: bool

    class Config:
        from_attributes = True