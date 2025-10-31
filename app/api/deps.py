from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..schemas import token as token_schema
from ..db.base import SessionLocal
from ..db.models import User, ProjectMember, ProjectRole, Issue
from ..core.config import settings
from ..crud import crud_user, crud_member, crud_issue

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
        token_data = token_schema.TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_project_member_from_path(
    project_id: UUID = Path(...),
    user_id: UUID = Path(...),
    db: Session = Depends(get_db)
) -> ProjectMember:
    """
    Dependency to get a specific project member from the URL path.
    """
    member = crud_member.get_project_member(db, project_id=project_id, user_id=user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")
    return member

def require_role(required_roles: List[ProjectRole]):
    """
    Dependency that creates a dependency to check for required roles.
    Assumes `project_id` is in the URL path.
    """
    def get_current_member(
        project_id: UUID = Path(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> ProjectMember:
        if current_user.is_superuser:
            # Create a mock ProjectMember object for superusers with an Admin role
            return ProjectMember(
                user_id=current_user.id,
                project_id=project_id,
                role=ProjectRole.ADMIN,
                user=current_user
            )

        member = crud_member.get_project_member(db, project_id=project_id, user_id=current_user.id)
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")
        
        if ProjectRole.ADMIN in required_roles and member.user.is_superuser:
            return member

        if member.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User role '{member.role.value}' is not authorized for this action")
            
        return member
    return get_current_member

def get_current_superuser(current_user: User = Depends(get_current_user)):
    """
    Dependency to ensure the current user is a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


# --- NEW DEPENDENCY TO FIX 422 ERROR ---

def require_issue_role(required_roles: List[ProjectRole]):
    """
    Dependency factory to check roles based on an `issue_id` in the path.
    It fetches the issue, finds its project, and then checks the user's role
    for that project.
    """
    def get_member_from_issue_path(
        issue_id: UUID = Path(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> ProjectMember:
        
        # 1. Get the issue from the path
        issue = crud_issue.get_issue(db, issue_id=issue_id)
        if not issue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
        
        # 2. Get the project_id from the issue
        project_id = issue.project_id

        # 3. Check role (similar logic to `require_role`)
        if current_user.is_superuser:
            return ProjectMember(
                user_id=current_user.id,
                project_id=project_id,
                role=ProjectRole.ADMIN,
                user=current_user
            )

        member = crud_member.get_project_member(db, project_id=project_id, user_id=current_user.id)
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")
        
        if ProjectRole.ADMIN in required_roles and member.user.is_superuser:
            return member

        if member.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User role '{member.role.value}' is not authorized for this action")
            
        return member
    return get_member_from_issue_path