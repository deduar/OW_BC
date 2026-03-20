from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status, Cookie
from sqlmodel import Session, select
from app.db import get_session
from app.models import AppUser, UserSession

def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> AppUser:
    if not session_token:
        # For now, if no token, we can't get user. 
        # But for development/MVP we might want a mock if needed.
        # Let's stick to strict for now.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    statement = select(UserSession).where(UserSession.session_token == session_token)
    user_session = session.exec(statement).first()
    
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    
    user = session.get(AppUser, user_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user

def get_tenant_id(
    current_user: Annotated[AppUser, Depends(get_current_user)]
) -> UUID:
    return current_user.tenant_id

CurrentTenantID = Annotated[UUID, Depends(get_tenant_id)]
SessionDep = Annotated[Session, Depends(get_session)]
