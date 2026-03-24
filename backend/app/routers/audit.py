from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.deps import get_session, CurrentTenantID
from app.models import AuditLogRecord
from app.schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    tenant_id: CurrentTenantID,
    session: Session = Depends(get_session),
    event_type: Optional[str] = None
):
    statement = select(AuditLogRecord).where(AuditLogRecord.tenant_id == tenant_id).order_by(AuditLogRecord.timestamp.desc())
    if event_type:
        statement = statement.where(AuditLogRecord.event_type == event_type)
    
    return session.exec(statement).all()
