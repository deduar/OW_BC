from typing import Optional, List
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    session_token: str
    token_type: str = "bearer"

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class FileUploadResponse(BaseModel):
    id: UUID
    filename: str
    type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReconciliationRunCreate(BaseModel):
    name: str = "Reconciliation Run"
    bank_upload_ids: List[str] = []
    admin_upload_id: str = ""

class ReconciliationRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    run_id: UUID
    bank_transaction_id: UUID
    admin_entry_id: UUID
    score: float
    explanation_json: Optional[str]
    status: str
    decision_type: Optional[str]
    decided_by: Optional[UUID]
    decided_at: Optional[datetime]
    created_at: datetime
    bank_transaction: Optional[dict] = None
    admin_entry: Optional[dict] = None

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]
    event_type: str
    description: str
    metadata_json: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
