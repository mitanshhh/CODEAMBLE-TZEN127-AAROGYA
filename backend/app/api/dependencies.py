from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from typing import Optional, List

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

from app.core.rbac import ROLE_PERMISSIONS

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role == UserRole.DEVELOPER:
            return current_user
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role"
            )
        return current_user

def require_role(allowed_roles: List[UserRole]):
    return RoleChecker(allowed_roles)

def require_permission(required_permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)):
        if current_user.role == UserRole.DEVELOPER:
            return current_user
            
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if required_permission not in user_permissions and "all" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role"
            )
        return current_user
    return permission_checker

def resolve_hospital_id(
    hospital_id: Optional[int] = Query(None, description="Hospital ID (Required for Admins/Devs)"),
    current_user: User = Depends(get_current_user)
) -> int:
    """
    Dependency to resolve the hospital_id for a request.
    If role is DISTRICT_ADMIN or DEVELOPER, accepts ?hospital_id=X query parameter to query any facility.
    For standard staff roles, strictly forces queries to current_user.hospital_id.
    """
    if current_user.role in [UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]:
        if not hospital_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hospital_id query parameter is required for administrators to scope this request."
            )
        return hospital_id
    
    if not current_user.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to any health centre."
        )
    return current_user.hospital_id
