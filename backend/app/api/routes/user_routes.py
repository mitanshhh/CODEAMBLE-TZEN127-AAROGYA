from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.api.dependencies import get_current_user, require_role, resolve_hospital_id
import secrets
import string

router = APIRouter()

def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DISTRICT_ADMIN, UserRole.MEDICAL_OFFICER]))
):
    # Check if username or email exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Only District Admin can assign to other hospitals or create other District Admins
    if current_user.role != UserRole.DISTRICT_ADMIN:
        if user_in.hospital_id != current_user.hospital_id:
            raise HTTPException(status_code=403, detail="Cannot create users for other hospitals")
        if user_in.role in [UserRole.DISTRICT_ADMIN, UserRole.DEVELOPER]:
            raise HTTPException(status_code=403, detail="Cannot create admin roles")

    pwd = user_in.password if user_in.password else generate_random_password()
    hashed = get_password_hash(pwd)

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        role=user_in.role,
        hospital_id=user_in.hospital_id,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # TODO: Send email with credentials using SMTP if needed
    return new_user
