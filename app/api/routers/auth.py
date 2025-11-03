from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from ...schemas import user as user_schema
from ...schemas import token as token_schema
from ...api.deps import get_db, get_current_user
from ...core.security import create_access_token, authenticate_user, get_password_hash, verify_password
from ...crud import crud_user
from ...db.models import User

router = APIRouter()

@router.post("/token", response_model=token_schema.Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        user=user
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=user_schema.User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user

@router.put("/users/me", response_model=user_schema.User)
def update_user_me(
    user_in: user_schema.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update own user.
    """
    # --- FIX HERE: Changed 'db_obj' to 'db_user' ---
    user = crud_user.update_user(db, db_user=current_user, user_in=user_in)
    return user

@router.put("/users/me/password")
def update_password_me(
    password_in: user_schema.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update own password.
    """
    if not verify_password(password_in.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    hashed_password = get_password_hash(password_in.new_password)
    current_user.password_hash = hashed_password
    db.add(current_user)
    db.commit()
    return {"message": "Password updated successfully"}
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...schemas import user as user_schema
from ...schemas import token as token_schema
from ...api.deps import get_db, get_current_user
from ...core.security import create_access_token, authenticate_user, get_password_hash, verify_password
from ...crud import crud_user
from ...db.models import User

router = APIRouter()

@router.post("/token", response_model=token_schema.Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        user=user
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=user_schema.User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user

@router.put("/users/me", response_model=user_schema.User)
def update_user_me(
    user_in: user_schema.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update own user.
    """
    # --- FIX HERE: Changed 'db_obj' to 'db_user' ---
    user = crud_user.update_user(db, db_user=current_user, user_in=user_in)
    return user

@router.put("/users/me/password")
def update_password_me(
    password_in: user_schema.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update own password.
    """
    if not verify_password(password_in.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    hashed_password = get_password_hash(password_in.new_password)
    current_user.password_hash = hashed_password
    db.add(current_user)
    db.commit()
    return {"message": "Password updated successfully"}