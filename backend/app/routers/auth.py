from datetime import datetime, timedelta, timezone
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlmodel import Session, select
from app.db import get_session
from app.models import AppUser, Tenant, UserSession
from app.schemas import UserCreate, UserResponse, LoginRequest, Token
from app.security import get_password_hash, verify_password

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

@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    response: Response,
    session: Session = Depends(get_session)
):
    statement = select(AppUser).where(AppUser.email == login_data.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Create session
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    
    user_session = UserSession(
        user_id=user.id,
        session_token=token,
        expires_at=expires_at
    )
    session.add(user_session)
    session.commit()
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        expires=expires_at
    )
    
    return Token(session_token=token)

@router.post("/logout")
def logout(
    response: Response,
    session: Session = Depends(get_session),
    session_token: Annotated[str | None, Cookie()] = None,
):
    if session_token:
        statement = select(UserSession).where(UserSession.session_token == session_token)
        db_session = session.exec(statement).first()
        if db_session:
            session.delete(db_session)
            session.commit()
    
    response.delete_cookie(key="session_token")
    return {"detail": "Successfully logged out"}
