from datetime import datetime, timedelta, timezone
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlmodel import Session, select
from app.db import get_session
from app.models import AppUser, Tenant, UserSession, PasswordResetToken
from app.schemas import UserCreate, UserResponse, LoginRequest, Token, PasswordResetRequest, PasswordResetConfirm
from app.security import get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(
    session_token: Annotated[str | None, Cookie()] = None,
    session: Session = Depends(get_session)
) -> AppUser:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    statement = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.expires_at > datetime.now(timezone.utc)
    )
    db_session = session.exec(statement).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    user = session.get(AppUser, db_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: AppUser = Depends(get_current_user)):
    return current_user

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

@router.post("/password-reset-request")
def request_password_reset(
    request_in: PasswordResetRequest,
    session: Session = Depends(get_session)
):
    statement = select(AppUser).where(AppUser.email == request_in.email)
    user = session.exec(statement).first()
    
    # Always return success to avoid user enumeration
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        session.add(reset_token)
        session.commit()
        
        # TODO: Send email with token
        print(f"DEBUG: Password reset token for {user.email}: {token}")
        
    return {"detail": "If the email exists, a reset link has been sent."}

@router.post("/password-reset-confirm")
def confirm_password_reset(
    confirm_in: PasswordResetConfirm,
    session: Session = Depends(get_session)
):
    statement = select(PasswordResetToken).where(
        PasswordResetToken.token == confirm_in.token,
        PasswordResetToken.used_at == None,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    )
    reset_token = session.exec(statement).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    user = session.get(AppUser, reset_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(confirm_in.new_password)
    session.add(user)
    
    # Mark token as used
    reset_token.used_at = datetime.now(timezone.utc)
    session.add(reset_token)
    
    # Invalidate all existing sessions for this user
    from sqlmodel import delete
    session.exec(delete(UserSession).where(UserSession.user_id == user.id))
    
    session.commit()
    
    return {"detail": "Password has been reset successfully"}
