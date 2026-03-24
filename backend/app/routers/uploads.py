import os
import shutil
import magic
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from app.deps import get_current_user, CurrentTenantID, SessionDep
from app.models import FileUpload
from app.schemas import FileUploadResponse
from app.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_BANK_TYPES = [
    "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain"
]

@router.post("/bank", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_bank_statement(
    file: UploadFile = File(...),
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    # Validate file content with magic bytes
    content_header = await file.read(2048)
    file_type = magic.from_buffer(content_header, mime=True)
    await file.seek(0)

    if file_type not in ALLOWED_BANK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content type: {file_type}. Allowed types: PDF, XLS, XLSX, CSV"
        )
    
    # Create DB record first
    file_id = uuid4()
    storage_path = os.path.join(str(tenant_id), f"{file_id}")
    
    db_file = FileUpload(
        id=file_id,
        tenant_id=tenant_id,
        original_filename=file.filename,
        file_type="bank",
        storage_path=storage_path,
        status="pending"
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    
    # Save file
    tenant_dir = Path(settings.UPLOAD_DIR) / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = tenant_dir / str(file_id)
    
    size = 0
    try:
        with file_path.open("wb") as buffer:
            while content := await file.read(1024 * 1024):  # Read in chunks of 1MB
                size += len(content)
                if size > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Cleanup
                    buffer.close()
                    file_path.unlink()
                    session.delete(db_file)
                    session.commit()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB"
                    )
                buffer.write(content)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        # If any other error, mark as failed in DB
        db_file.status = "failed"
        db_file.error_message = str(e)
        session.add(db_file)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    return db_file

@router.post("/admin", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_admin_report(
    file: UploadFile = File(...),
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    # Admin reports are usually CSV/XLS/XLSX
    ALLOWED_ADMIN_TYPES = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/plain"
    ]
    
    # Validate file content with magic bytes
    content_header = await file.read(2048)
    file_type = magic.from_buffer(content_header, mime=True)
    await file.seek(0)
    
    if file_type not in ALLOWED_ADMIN_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content type: {file_type}. Allowed types: XLS, XLSX, CSV"
        )
    
    file_id = uuid4()
    storage_path = os.path.join(str(tenant_id), f"{file_id}")
    
    db_file = FileUpload(
        id=file_id,
        tenant_id=tenant_id,
        original_filename=file.filename,
        file_type="admin",
        storage_path=storage_path,
        status="pending"
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    
    # Save file
    tenant_dir = Path(settings.UPLOAD_DIR) / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = tenant_dir / str(file_id)
    
    size = 0
    try:
        with file_path.open("wb") as buffer:
            while content := await file.read(1024 * 1024):
                size += len(content)
                if size > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    file_path.unlink()
                    session.delete(db_file)
                    session.commit()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB"
                    )
                buffer.write(content)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        db_file.status = "failed"
        db_file.error_message = str(e)
        session.add(db_file)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    return db_file

@router.get("/", response_model=list[FileUploadResponse])
async def list_uploads(
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    from sqlmodel import select
    statement = select(FileUpload).where(FileUpload.tenant_id == tenant_id).order_by(FileUpload.upload_timestamp.desc())
    uploads = session.exec(statement).all()
    return uploads
