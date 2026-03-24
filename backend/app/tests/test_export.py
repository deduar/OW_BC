import pytest
import io
import csv
import asyncio
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel
from app.models import ReconciliationRun, Match, BankTransaction, AdminEntry, ExportRecord, AppUser
from app.routers.reconciliation import export_run_csv

# Setup in-memory SQLite for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_export_csv_content(session):
    tenant_id = uuid4()
    user_id = uuid4()
    user = AppUser(id=user_id, email="test@test.com", hashed_password="...", tenant_id=tenant_id)
    session.add(user)
    
    run = ReconciliationRun(id=uuid4(), tenant_id=tenant_id, name="Test Run", status="ready")
    session.add(run)
    
    # 1. Reconciled match
    bt1 = BankTransaction(id=uuid4(), tenant_id=tenant_id, upload_id=uuid4(), date=datetime(2025,1,1), amount=100.0, description="Match 1")
    ae1 = AdminEntry(id=uuid4(), tenant_id=tenant_id, upload_id=uuid4(), date=datetime(2025,1,1), amount=100.0, description="Match 1")
    session.add_all([bt1, ae1])
    session.commit()
    
    match1 = Match(
        id=uuid4(), tenant_id=tenant_id, run_id=run.id, 
        bank_transaction_id=bt1.id, admin_entry_id=ae1.id,
        status="matched", score=100.0, decision_type="auto"
    )
    
    # 2. Suggested match
    bt2 = BankTransaction(id=uuid4(), tenant_id=tenant_id, upload_id=uuid4(), date=datetime(2025,1,2), amount=200.0, description="Match 2")
    ae2 = AdminEntry(id=uuid4(), tenant_id=tenant_id, upload_id=uuid4(), date=datetime(2025,1,2), amount=200.5, description="Match 2 approx")
    session.add_all([bt2, ae2])
    session.commit()
    
    match2 = Match(
        id=uuid4(), tenant_id=tenant_id, run_id=run.id, 
        bank_transaction_id=bt2.id, admin_entry_id=ae2.id,
        status="suggested", score=75.0, decision_type="auto"
    )
    
    # 3. Pending (unmatched) transactions
    bt3 = BankTransaction(id=uuid4(), tenant_id=tenant_id, upload_id=uuid4(), date=datetime(2025,1,3), amount=300.0, description="Unmatched Bank")
    ae3 = AdminEntry(id=uuid4(), tenant_id=tenant_id, upload_id=uuid4(), date=datetime(2025,1,4), amount=400.0, description="Unmatched Admin")
    
    session.add_all([match1, match2, bt3, ae3])
    session.commit()
    
    # Mocking the FastAPI dependency call by passing user and session directly
    response = export_run_csv(run_id=run.id, user=user, session=session)
    
    # Collect content from StreamingResponse
    async def collect():
        content = ""
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                content += chunk.decode("utf-8")
            else:
                content += chunk
        return content
        
    content = asyncio.run(collect())
            
    # Parse CSV
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    
    assert len(rows) == 4
    
    # Check sections
    statuses = [r["Match Status"] for r in rows]
    assert "matched" in statuses
    assert "suggested" in statuses
    assert statuses.count("pending") == 2
    
    # Verify specific content
    matched_row = next(r for r in rows if r["Match Status"] == "matched")
    assert matched_row["Bank Description"] == "Match 1"
    assert matched_row["Admin Description"] == "Match 1"
    
    pending_bank = next(r for r in rows if r["Bank Description"] == "Unmatched Bank")
    assert pending_bank["Match Status"] == "pending"
    assert pending_bank["Admin Description"] == ""
    
    pending_admin = next(r for r in rows if r["Admin Description"] == "Unmatched Admin")
    assert pending_admin["Match Status"] == "pending"
    assert pending_admin["Bank Description"] == ""
