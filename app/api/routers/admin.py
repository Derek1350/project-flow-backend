from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ...api.deps import get_db, get_current_superuser
from ...crud import crud_user
from ...schemas import user as user_schema
from ...db.models import User

router = APIRouter()

@router.get("/admin/users", response_model=List[user_schema.User])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Retrieve all users. Admin only.
    """
    return crud_user.get_users(db)

@router.post("/admin/users", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user_in: user_schema.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Create new user. Admin only.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud_user.create_user(db, user_in=user_in)
    return user

@router.put("/admin/users/{user_id}", response_model=user_schema.User)
def update_user_privileges(
    user_id: uuid.UUID,
    user_in: user_schema.UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Update a user's privileges (e.g., make them a superuser). Admin only.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent an admin from accidentally removing their own superuser status
    if current_user.id == db_user.id and user_in.is_superuser is False: # Check for explicit False
        raise HTTPException(status_code=400, detail="Admins cannot remove their own superuser status.")

    # Directly update the user object with the provided data
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# --- NEW ENDPOINT for editing details ---
@router.put("/admin/users/{user_id}/details", response_model=user_schema.User)
def update_user_details_by_admin(
    user_id: uuid.UUID,
    user_in: user_schema.UserAdminFullUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Update a user's details (email, name, password). Admin only.
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # If email is being changed, check if the new one is taken
    if user_in.email and user_in.email != db_user.email:
        existing_user = crud_user.get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="This email is already registered.")

    # The updated crud_user.update_user function handles password hashing
    return crud_user.update_user(db, db_user=db_user, user_in=user_in)


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Delete a user. Admin only.
    """
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Admins cannot delete their own account.")
    
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    crud_user.delete_user(db, user_id=user_id)
    return