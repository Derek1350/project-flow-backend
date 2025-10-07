from sqlalchemy.orm import Session
from sqlalchemy import select, update
from db.models import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash

def get_user_by_email(db: Session, email: str) -> User | None:
    """Gets a user from the database by their email address."""
    result = db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Gets all users from the database."""
    result = db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

def create_user(db: Session, user_in: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    """Updates a user's information."""
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
