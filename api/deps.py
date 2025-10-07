from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from schemas import token as token_schema
from db.base import SessionLocal
from db.models import User
from core.config import settings
import crud.crud_user as crud_user

# This tells FastAPI where to get the token from the request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def get_db():
    """
    Dependency function to get a database session.
    Yields a session for a single request-response cycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current user from a JWT token.
    Decodes the token, validates it, and fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # Corrected class name from TokenPayload to TokenData
        token_data = token_schema.TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

