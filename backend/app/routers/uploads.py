import os
import hashlib
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
    "text/plain",
    "text/html"
]


def calculate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def check_existing_file(session, tenant_id, filename: str, file_hash: str, file_type: str):
    import logging
    from sqlmodel import select
    statement = select(FileUpload).where(
        FileUpload.tenant_id == tenant_id,
        FileUpload.original_filename == filename,
        FileUpload.content_hash == file_hash,
        FileUpload.file_type == file_type,
        FileUpload.status == "succeeded"
    )
    existing = session.exec(statement).first()
    logging.warning(f"[UPLOAD] check_existing_file: tenant={tenant_id}, filename={filename}, hash={file_hash[:20] if file_hash else 'None'}..., type={file_type}, found={existing is not None}")
    return existing


@router.post("/bank", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_bank_statement(
    file: UploadFile = File(...),
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    content_header = await file.read(2048)
    file_type = magic.from_buffer(content_header, mime=True)
    await file.seek(0)

    if file_type not in ALLOWED_BANK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content type: {file_type}. Allowed types: PDF, XLS, XLSX, CSV"
        )
    
    file_content = b""
    size = 0
    try:
        while content := await file.read(1024 * 1024):
            size += len(content)
            if size > settings.MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB"
                )
            file_content += content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read file: {str(e)}"
        )
    
    file_hash = calculate_file_hash(file_content)
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"[UPLOAD] Calculated hash for '{file.filename}': {file_hash}")
    
    # Use raw connection to query - bypass ORM caching
    from app.db import engine
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("SELECT original_filename, content_hash, status FROM fileupload"))
        rows = result.fetchall()
        logger.warning(f"[UPLOAD] Raw SQL - All files in DB: {rows}")
    
    # Also check with session
    session.expire_all()
    from sqlmodel import select
    from app.models import FileUpload
    all_files = session.exec(select(FileUpload)).all()
    logger.warning(f"[UPLOAD] Session query - All files in DB: {[(f.original_filename, f.content_hash, f.status) for f in all_files]}")
    
    existing = check_existing_file(session, tenant_id, file.filename, file_hash, "bank")
    if existing:
        logger.warning(f"[UPLOAD] Duplicate detected! File '{file.filename}' already processed. Returning existing ID: {existing.id}")
        return FileUploadResponse(
            id=existing.id,
            filename=existing.original_filename,
            type=existing.file_type,
            status="already_processed",
            error_message=None,
            created_at=existing.upload_timestamp
        )
    
    logger.warning(f"[UPLOAD] New file '{file.filename}' - processing...")
    
    file_id = uuid4()
    storage_path = os.path.join(str(tenant_id), f"{file_id}")
    
    db_file = FileUpload(
        id=file_id,
        tenant_id=tenant_id,
        original_filename=file.filename,
        file_type="bank",
        storage_path=storage_path,
        content_hash=file_hash,
        status="pending"
    )
    session.add(db_file)
    session.commit()
    
    tenant_dir = Path(settings.UPLOAD_DIR) / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    file_path = tenant_dir / str(file_id)
    
    try:
        with file_path.open("wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        db_file.status = "failed"
        db_file.error_message = str(e)
        session.add(db_file)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    try:
        from app.parsers.csv_parser import parse_bank_csv
        from app.parsers.excel_parser import parse_bank_excel
        from app.parsers.pdf_parser import parse_bank_pdf
        
        transactions = []
        if file_type == "text/csv" or file.filename.lower().endswith(".csv"):
            transactions = parse_bank_csv(file_content, str(tenant_id), str(file_id))
        elif file_type == "text/html" or file.filename.lower().endswith((".xls", ".xlsx")):
            transactions = parse_bank_excel(file_content, file.filename, str(tenant_id), str(file_id))
        elif file_type == "application/pdf":
            transactions = parse_bank_pdf(file_content, file.filename, str(tenant_id), str(file_id))
        elif file_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            transactions = parse_bank_excel(file_content, file.filename, str(tenant_id), str(file_id))
        
        for tx in transactions:
            session.add(tx)
        
        db_file.status = "succeeded"
        session.add(db_file)
        session.commit()
    except Exception as e:
        db_file.status = "failed"
        db_file.error_message = f"Parse error: {str(e)}"
        session.add(db_file)
        session.commit()
    
    session.refresh(db_file)
    return FileUploadResponse(
        id=db_file.id,
        filename=db_file.original_filename,
        type=db_file.file_type,
        status=db_file.status,
        error_message=db_file.error_message,
        created_at=db_file.upload_timestamp
    )

@router.post("/admin", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_admin_report(
    file: UploadFile = File(...),
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    ALLOWED_ADMIN_TYPES = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/plain"
    ]
    
    content_header = await file.read(2048)
    file_type = magic.from_buffer(content_header, mime=True)
    await file.seek(0)
    
    if file_type not in ALLOWED_ADMIN_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content type: {file_type}. Allowed types: XLS, XLSX, CSV"
        )
    
    file_content = b""
    size = 0
    try:
        while content := await file.read(1024 * 1024):
            size += len(content)
            if size > settings.MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB"
                )
            file_content += content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read file: {str(e)}"
        )
    
    file_hash = calculate_file_hash(file_content)
    
    existing = check_existing_file(session, tenant_id, file.filename, file_hash, "admin")
    if existing:
        return FileUploadResponse(
            id=existing.id,
            filename=existing.original_filename,
            type=existing.file_type,
            status="already_processed",
            error_message=None,
            created_at=existing.upload_timestamp
        )
    
    file_id = uuid4()
    storage_path = os.path.join(str(tenant_id), f"{file_id}")
    
    db_file = FileUpload(
        id=file_id,
        tenant_id=tenant_id,
        original_filename=file.filename,
        file_type="admin",
        storage_path=storage_path,
        content_hash=file_hash,
        status="pending"
    )
    session.add(db_file)
    session.commit()
    
    tenant_dir = Path(settings.UPLOAD_DIR) / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = tenant_dir / str(file_id)
    
    try:
        with file_path.open("wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        db_file.status = "failed"
        db_file.error_message = str(e)
        session.add(db_file)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    try:
        from app.parsers.admin_parser import parse_admin_report_xlsx
        
        entries = parse_admin_report_xlsx(file_content, str(tenant_id), str(file_id))
        
        for entry in entries:
            session.add(entry)
        
        db_file.status = "succeeded"
        session.add(db_file)
        session.commit()
    except Exception as e:
        db_file.status = "failed"
        db_file.error_message = f"Parse error: {str(e)}"
        session.add(db_file)
        session.commit()
    
    session.refresh(db_file)
    return FileUploadResponse(
        id=db_file.id,
        filename=db_file.original_filename,
        type=db_file.file_type,
        status=db_file.status,
        error_message=db_file.error_message,
        created_at=db_file.upload_timestamp
    )

@router.get("", response_model=list[FileUploadResponse])
async def list_uploads(
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    from sqlmodel import select
    statement = select(FileUpload).where(FileUpload.tenant_id == tenant_id).order_by(FileUpload.upload_timestamp.desc())
    uploads = session.exec(statement).all()
    
    result = []
    for u in uploads:
        result.append(FileUploadResponse(
            id=u.id,
            filename=u.original_filename,
            type=u.file_type,
            status=u.status,
            error_message=u.error_message,
            created_at=u.upload_timestamp
        ))
    return result


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    file_id: UUID,
    session: SessionDep = None,
    tenant_id: CurrentTenantID = None
):
    from sqlmodel import select
    from app.models import BankTransaction, AdminEntry, Match
    
    statement = select(FileUpload).where(
        FileUpload.id == file_id,
        FileUpload.tenant_id == tenant_id
    )
    db_file = session.exec(statement).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete associated transactions and matches
    if db_file.file_type == "bank":
        # Get all bank transactions from this upload
        tx_stmt = select(BankTransaction).where(BankTransaction.upload_id == file_id)
        transactions = session.exec(tx_stmt).all()
        for tx in transactions:
            # Delete matches for this transaction
            match_stmt = select(Match).where(Match.bank_transaction_id == tx.id)
            matches = session.exec(match_stmt).all()
            for m in matches:
                session.delete(m)
            session.delete(tx)
    else:
        # Get all admin entries from this upload
        entry_stmt = select(AdminEntry).where(AdminEntry.upload_id == file_id)
        entries = session.exec(entry_stmt).all()
        for entry in entries:
            # Delete matches for this entry
            match_stmt = select(Match).where(Match.admin_entry_id == entry.id)
            matches = session.exec(match_stmt).all()
            for m in matches:
                session.delete(m)
            session.delete(entry)
    
    # Delete the file record
    session.delete(db_file)
    session.commit()
    
    # Optionally delete the physical file
    file_path = Path(settings.UPLOAD_DIR) / str(tenant_id) / str(file_id)
    if file_path.exists():
        file_path.unlink()
    
    return None
