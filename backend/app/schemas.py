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
    original_filename: str
    file_type: str
    status: str
    upload_timestamp: datetime

    class Config:
        from_attributes = True

class ReconciliationRunCreate(BaseModel):
    name: str

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

    class Config:
        from_attributes = True
