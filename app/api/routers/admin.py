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
    if current_user.id == db_user.id and not user_in.is_superuser:
        raise HTTPException(status_code=400, detail="Admins cannot remove their own superuser status.")

    # Directly update the user object with the provided data
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user
