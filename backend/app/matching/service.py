import json
from uuid import UUID
from typing import List, Optional
from sqlmodel import Session, select
from app.models import BankTransaction, AdminEntry, Match, ReconciliationRun
from app.matching.engine import MatchingEngine, MatchConfig

class MatchingService:
    def __init__(self, session: Session, config: Optional[MatchConfig] = None):
        self.session = session
        self.engine = MatchingEngine(config)

    def run_reconciliation(self, run_id: UUID, tenant_id: UUID):
        # 1. Fetch unmatched bank transactions for this tenant/upload
        # In a real scenario, a run might be linked to specific uploads.
        # For now, let's assume we match all pending for the tenant.
        
        # We need a way to identify which transactions belong to this "run"
        # Usually, a run is created from specific bank files and admin files.
        # But for the MVP, let's just get everything that is not already matched.
        
        bank_stmt = select(BankTransaction).where(
            BankTransaction.tenant_id == tenant_id,
            ~select(Match).where(Match.bank_transaction_id == BankTransaction.id, Match.status == "matched").exists()
        )
        bank_txs = self.session.exec(bank_stmt).all()
        
        admin_stmt = select(AdminEntry).where(
            AdminEntry.tenant_id == tenant_id,
            ~select(Match).where(Match.admin_entry_id == AdminEntry.id, Match.status == "matched").exists()
        )
        admin_entries = self.session.exec(admin_stmt).all()
        
        for bank_tx in bank_txs:
            candidates = self.engine.find_candidates(bank_tx, admin_entries)
            
            if not candidates:
                continue
                
            best = candidates[0]
            
            if best.score >= self.engine.config.auto_match_threshold:
                # Create a match
                match = Match(
                    tenant_id=tenant_id,
                    run_id=run_id,
                    bank_transaction_id=bank_tx.id,
                    admin_entry_id=UUID(best.admin_entry_id),
                    score=best.score,
                    explanation_json=best.explanation.model_dump_json(),
                    status="matched",
                    decision_type="auto"
                )
                self.session.add(match)
                # Remove from available entries for this run to avoid double matching in the same loop
                # (Simple greedy approach for now)
                admin_entries = [ae for ae in admin_entries if str(ae.id) != best.admin_entry_id]
            else:
                # Create suggested matches for top-N
                for cand in candidates:
                    match = Match(
                        tenant_id=tenant_id,
                        run_id=run_id,
                        bank_transaction_id=bank_tx.id,
                        admin_entry_id=UUID(cand.admin_entry_id),
                        score=cand.score,
                        explanation_json=cand.explanation.model_dump_json(),
                        status="suggested",
                        decision_type="auto"
                    )
                    self.session.add(match)
                    
        self.session.commit()
