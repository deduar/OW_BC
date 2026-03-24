from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.deps import get_session, CurrentTenantID, get_current_user
from app.models import ReconciliationRun, Match, AuditLogRecord, AppUser, ExportRecord, BankTransaction, AdminEntry
from app.schemas import ReconciliationRunCreate, ReconciliationRunResponse, MatchResponse
from app.matching.service import MatchingService
import json
import io
import csv

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])

@router.post("/runs", response_model=ReconciliationRunResponse, status_code=status.HTTP_201_CREATED)
def create_reconciliation_run(
    run_in: ReconciliationRunCreate,
    user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    tenant_id = user.tenant_id
    new_run = ReconciliationRun(
        tenant_id=tenant_id,
        name=run_in.name,
        status="matching"
    )
    session.add(new_run)
    session.commit()
    session.refresh(new_run)
    
    # Run the matching engine with selected uploads
    service = MatchingService(session)
    service.run_reconciliation(
        new_run.id, 
        tenant_id,
        bank_upload_ids=run_in.bank_upload_ids,
        admin_upload_id=run_in.admin_upload_id if run_in.admin_upload_id else None
    )
    
    # Update status to ready
    new_run.status = "ready"
    session.add(new_run)
    
    # Audit log
    audit = AuditLogRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="RECONCILIATION_RUN_CREATED",
        description=f"Reconciliation run '{new_run.name}' created and matching completed.",
        metadata_json=json.dumps({"run_id": str(new_run.id)})
    )
    session.add(audit)
    
    session.commit()
    session.refresh(new_run)
    
    return new_run

@router.get("/runs", response_model=List[ReconciliationRunResponse])
def list_reconciliation_runs(
    tenant_id: CurrentTenantID,
    session: Session = Depends(get_session)
):
    statement = select(ReconciliationRun).where(ReconciliationRun.tenant_id == tenant_id)
    return session.exec(statement).all()

@router.get("/runs/{run_id}/matches", response_model=List[MatchResponse])
def list_matches(
    run_id: UUID,
    tenant_id: CurrentTenantID,
    session: Session = Depends(get_session),
    status_filter: Optional[str] = None
):
    statement = select(Match).where(
        Match.run_id == run_id,
        Match.tenant_id == tenant_id
    )
    if status_filter:
        statement = statement.where(Match.status == status_filter)
    
    return session.exec(statement).all()

@router.post("/matches/{match_id}/confirm", response_model=MatchResponse)
def confirm_match(
    match_id: UUID,
    user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    tenant_id = user.tenant_id
    match = session.get(Match, match_id)
    if not match or match.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.status == "matched":
        return match
        
    # Enforce no double reconciliation (Task 7.3)
    already_matched_bank = session.exec(
        select(Match).where(
            Match.bank_transaction_id == match.bank_transaction_id,
            Match.status == "matched",
            Match.id != match.id
        )
    ).first()
    if already_matched_bank:
        raise HTTPException(status_code=400, detail="Bank transaction already matched")
        
    already_matched_admin = session.exec(
        select(Match).where(
            Match.admin_entry_id == match.admin_entry_id,
            Match.status == "matched",
            Match.id != match.id
        )
    ).first()
    if already_matched_admin:
        raise HTTPException(status_code=400, detail="Admin entry already matched")
        
    match.status = "matched"
    match.decision_type = "manual"
    match.decided_by = user.id
    
    session.add(match)
    
    # Audit log
    audit = AuditLogRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="MATCH_CONFIRMED",
        description=f"Match {match.id} manually confirmed.",
        metadata_json=json.dumps({"match_id": str(match.id), "bank_tx_id": str(match.bank_transaction_id), "admin_entry_id": str(match.admin_entry_id)})
    )
    session.add(audit)
    
    # Optional: Reject other suggestions for this bank tx or admin entry
    other_suggestions_stmt = select(Match).where(
        ((Match.bank_transaction_id == match.bank_transaction_id) | (Match.admin_entry_id == match.admin_entry_id)),
        Match.status == "suggested",
        Match.id != match.id
    )
    other_suggestions = session.exec(other_suggestions_stmt).all()
    for other in other_suggestions:
        other.status = "rejected"
        session.add(other)
        
    session.commit()
    session.refresh(match)
    return match

@router.post("/matches/{match_id}/reject", response_model=MatchResponse)
def reject_match(
    match_id: UUID,
    user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    tenant_id = user.tenant_id
    match = session.get(Match, match_id)
    if not match or match.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match.status = "rejected"
    match.decision_type = "manual"
    match.decided_by = user.id
    
    session.add(match)
    
    # Audit log
    audit = AuditLogRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="MATCH_REJECTED",
        description=f"Match {match.id} manually rejected.",
        metadata_json=json.dumps({"match_id": str(match.id)})
    )
    session.add(audit)
    
    session.commit()
    session.refresh(match)
    return match

@router.get("/runs/{run_id}/export/csv")
def export_run_csv(
    run_id: UUID,
    user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    tenant_id = user.tenant_id
    run = session.get(ReconciliationRun, run_id)
    if not run or run.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Run not found")
        
    # Matches (matched/suggested/rejected)
    matches = session.exec(select(Match).where(Match.run_id == run_id)).all()
    matched_bank_ids = {m.bank_transaction_id for m in matches if m.bank_transaction_id}
    matched_admin_ids = {m.admin_entry_id for m in matches if m.admin_entry_id}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Match Status", "Score", "Bank Date", "Bank Description", "Bank Amount", 
        "Admin Date", "Admin Description", "Admin Amount", "Decision Type", "Explanation"
    ])
    
    # 1. Export actual matches
    for m in matches:
        bank_tx = session.get(BankTransaction, m.bank_transaction_id)
        admin_e = session.get(AdminEntry, m.admin_entry_id)
        
        writer.writerow([
            m.status,
            m.score,
            bank_tx.date.strftime("%Y-%m-%d") if bank_tx else "",
            bank_tx.description if bank_tx else "",
            bank_tx.amount if bank_tx else "",
            admin_e.date.strftime("%Y-%m-%d") if admin_e else "",
            admin_e.description if admin_e else "",
            admin_e.amount if admin_e else "",
            m.decision_type,
            m.explanation_json
        ])
    
    # 2. Export unmatched bank transactions as 'pending'
    # For now, we consider all bank transactions of the tenant that are not matched in ANY run
    # (Matching the logic in MatchingService.run_reconciliation)
    unmatched_bank = session.exec(select(BankTransaction).where(
        BankTransaction.tenant_id == tenant_id,
        ~select(Match).where(Match.bank_transaction_id == BankTransaction.id, Match.status == "matched").exists(),
        BankTransaction.id.not_in(matched_bank_ids) if matched_bank_ids else True
    )).all()
    
    for bt in unmatched_bank:
        writer.writerow([
            "pending",
            0.0,
            bt.date.strftime("%Y-%m-%d"),
            bt.description,
            bt.amount,
            "", "", "",
            "none",
            "No candidates found"
        ])
        
    # 3. Export unmatched admin entries as 'pending'
    unmatched_admin = session.exec(select(AdminEntry).where(
        AdminEntry.tenant_id == tenant_id,
        ~select(Match).where(Match.admin_entry_id == AdminEntry.id, Match.status == "matched").exists(),
        AdminEntry.id.not_in(matched_admin_ids) if matched_admin_ids else True
    )).all()
    
    for ae in unmatched_admin:
        writer.writerow([
            "pending",
            0.0,
            "", "", "",
            ae.date.strftime("%Y-%m-%d"),
            ae.description,
            ae.amount,
            "none",
            "No candidates found"
        ])
        
    file_name = f"reconciliation_export_{run_id}.csv"
    export_rec = ExportRecord(
        tenant_id=tenant_id,
        run_id=run_id,
        file_name=file_name,
        export_type="csv"
    )
    session.add(export_rec)
    
    audit = AuditLogRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="RECONCILIATION_EXPORTED",
        description=f"CSV Export generated for run '{run.name}'.",
        metadata_json=json.dumps({"run_id": str(run_id), "export_id": str(export_rec.id)})
    )
    session.add(audit)
    session.commit()
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )
