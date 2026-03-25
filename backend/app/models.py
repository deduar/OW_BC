from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class Tenant(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AppUser(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLogRecord(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="appuser.id", index=True)
    event_type: str = Field(index=True)
    description: str
    metadata_json: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="appuser.id", index=True)
    session_token: str = Field(index=True, unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PasswordResetToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="appuser.id", index=True)
    token: str = Field(index=True, unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used_at: Optional[datetime] = None


class FileUpload(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    original_filename: str
    file_type: str = Field(index=True)  # "bank" or "admin"
    storage_path: str
    content_hash: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="pending", index=True)  # pending, processing, succeeded, failed
    error_message: Optional[str] = None
    metadata_json: Optional[str] = None
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BankTransaction(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    upload_id: UUID = Field(foreign_key="fileupload.id", index=True)
    date: datetime = Field(index=True)
    amount: float = Field(index=True)
    description: str = Field(index=True)
    reference_raw: Optional[str] = Field(default=None, index=True)
    reference_normalized: Optional[str] = Field(default=None, index=True)
    raw_row_json: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AdminEntry(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    upload_id: UUID = Field(foreign_key="fileupload.id", index=True)
    date: datetime = Field(index=True)
    amount: float = Field(index=True)
    description: str = Field(index=True)
    reference_raw: Optional[str] = Field(default=None, index=True)
    reference_normalized: Optional[str] = Field(default=None, index=True)
    raw_row_json: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReconciliationRun(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    name: str
    status: str = Field(default="pending", index=True)  # pending, matching, ready, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Match(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    run_id: UUID = Field(foreign_key="reconciliationrun.id", index=True)
    bank_transaction_id: UUID = Field(foreign_key="banktransaction.id", index=True)
    admin_entry_id: UUID = Field(foreign_key="adminentry.id", index=True)
    score: float = Field(index=True)
    explanation_json: Optional[str] = None
    status: str = Field(default="suggested", index=True)  # matched, suggested, rejected
    decision_type: Optional[str] = None  # auto, manual
    decided_by: Optional[UUID] = Field(default=None, foreign_key="appuser.id")
    decided_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExportRecord(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    run_id: UUID = Field(foreign_key="reconciliationrun.id", index=True)
    file_name: str
    export_type: str = Field(index=True)  # "csv"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
