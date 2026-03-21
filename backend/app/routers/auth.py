from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db import get_session
from app.models import AppUser, Tenant
from app.schemas import UserCreate, UserResponse
from app.security import get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    # Check if user already exists
    statement = select(AppUser).where(AppUser.email == user_in.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Create tenant
    new_tenant = Tenant(name=user_in.tenant_name)
    session.add(new_tenant)
    session.commit()
    session.refresh(new_tenant)
    
    # Create user
    new_user = AppUser(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        tenant_id=new_tenant.id
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user
