import pytest
from datetime import datetime
from uuid import uuid4
from app.models import BankTransaction, AdminEntry
from app.matching.engine import MatchingEngine, MatchConfig

@pytest.fixture
def engine():
    return MatchingEngine()

def test_perfect_match(engine):
    bt = BankTransaction(
        id=uuid4(),
        tenant_id=uuid4(),
        upload_id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=25973.02,
        description="TPBW J0050205216 01080",
        reference_raw="4554"
    )
    ae = AdminEntry(
        id=uuid4(),
        tenant_id=uuid4(),
        upload_id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=25973.02,
        description="J0050205216 01080",
        reference_raw="4554"
    )
    
    score, explanation = engine.score(bt, ae)
    assert explanation.amount_match is True
    assert explanation.date_delta_days == 0
    assert explanation.description_similarity >= 90
    assert explanation.reference_substring_match is True
    assert score >= 100 # In our case weights are 40+20+20+40 = 120 max

def test_date_tolerance(engine):
    bt = BankTransaction(
        id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=100.0,
        description="test",
        tenant_id=uuid4(), upload_id=uuid4()
    )
    ae = AdminEntry(
        id=uuid4(),
        date=datetime(2025, 7, 20), # 2 days diff
        amount=100.0,
        description="test",
        tenant_id=uuid4(), upload_id=uuid4()
    )
    
    score, explanation = engine.score(bt, ae)
    assert explanation.date_delta_days == 2
    assert explanation.date_score > 0
    
    ae_far = AdminEntry(
        id=uuid4(),
        date=datetime(2025, 7, 22), # 4 days diff
        amount=100.0,
        description="test",
        tenant_id=uuid4(), upload_id=uuid4()
    )
    score_far, explanation_far = engine.score(bt, ae_far)
    assert explanation_far.date_delta_days == 4
    assert explanation_far.date_score == 0

def test_referencia_substring(engine):
    bt = BankTransaction(
        id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=100.0,
        description="PAGO MOVIL CCE 04249320499",
        reference_raw="51243258426",
        tenant_id=uuid4(), upload_id=uuid4()
    )
    ae = AdminEntry(
        id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=100.0,
        description="CLIENTE X",
        reference_raw="9320499", # Substring of description digits
        tenant_id=uuid4(), upload_id=uuid4()
    )
    
    score, explanation = engine.score(bt, ae)
    assert explanation.reference_substring_match is True
    assert explanation.reference_score == 40.0

def test_auto_match_threshold(engine):
    bt = BankTransaction(
        id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=100.0,
        description="test 123456",
        tenant_id=uuid4(), upload_id=uuid4()
    )
    ae = AdminEntry(
        id=uuid4(),
        date=datetime(2025, 7, 18),
        amount=100.0,
        description="test",
        reference_raw="123456",
        tenant_id=uuid4(), upload_id=uuid4()
    )
    
    score, _ = engine.score(bt, ae)
    assert score >= engine.config.auto_match_threshold
