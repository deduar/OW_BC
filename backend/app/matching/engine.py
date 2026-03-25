from typing import List, Optional, Tuple
from pydantic import BaseModel
from rapidfuzz import fuzz
from datetime import timedelta
from app.models import BankTransaction, AdminEntry
from app.utils.normalization import normalize_description, normalize_reference

class MatchConfig(BaseModel):
    date_tolerance_days: int = 5
    amount_tolerance_cents: float = 0.01
    auto_match_threshold: float = 70.0
    min_suggestion_threshold: float = 30.0
    
    weight_amount: float = 25.0
    weight_date: float = 15.0
    weight_description: float = 10.0
    weight_reference: float = 60.0

class ScoringExplanation(BaseModel):
    amount_match: bool
    amount_score: float
    date_delta_days: int
    date_score: float
    description_similarity: float
    description_score: float
    reference_substring_match: bool
    reference_in_bank_ref: bool
    reference_in_bank_desc: bool
    reference_score: float
    total_score: float

class MatchCandidate(BaseModel):
    bank_transaction_id: str
    admin_entry_id: str
    score: float
    explanation: ScoringExplanation

class MatchingEngine:
    def __init__(self, config: Optional[MatchConfig] = None):
        self.config = config or MatchConfig()

    def _check_reference_match(self, admin_ref: str, bank_ref: str, bank_desc: str) -> Tuple[bool, bool, bool]:
        """
        Check if admin reference is substring of bank reference or description.
        Returns (matched, in_bank_ref, in_bank_desc)
        
        IMPORTANT: Only match if reference is found in bank REFERENCE field, not description.
        The description may contain incidental digit sequences that match incorrectly.
        """
        admin_digits = normalize_reference(admin_ref or "")
        
        if not admin_digits or len(admin_digits) < 4:
            return False, False, False
        
        bank_ref_digits = normalize_reference(bank_ref or "")
        bank_desc_digits = normalize_reference(bank_desc or "")
        
        in_ref = admin_digits in bank_ref_digits if bank_ref_digits else False
        in_desc = admin_digits in bank_desc_digits if bank_desc_digits else False
        
        return in_ref, in_ref, in_desc

    def score(self, bank_tx: BankTransaction, admin_entry: AdminEntry) -> Tuple[float, ScoringExplanation]:
        # 1. Reference match (most important)
        ref_match, in_bank_ref, in_bank_desc = self._check_reference_match(
            admin_entry.reference_raw or "",
            bank_tx.reference_raw or "",
            bank_tx.description or ""
        )
        
        ref_score = self.config.weight_reference if ref_match else 0.0
        
        # 2. Amount match
        amount_match = abs(bank_tx.amount - admin_entry.amount) <= self.config.amount_tolerance_cents
        amount_score = self.config.weight_amount if amount_match else 0.0
        
        # 3. Date match
        delta = abs((bank_tx.date - admin_entry.date).days)
        date_score = 0.0
        if delta <= self.config.date_tolerance_days:
            date_score = self.config.weight_date * (1 - (delta / (self.config.date_tolerance_days + 1)))
        
        # 4. Description similarity
        norm_bank = normalize_description(bank_tx.description)
        norm_admin = normalize_description(admin_entry.description)
        similarity = fuzz.token_sort_ratio(norm_bank, norm_admin)
        description_score = (similarity / 100.0) * self.config.weight_description
        
        # If reference matches, boost score significantly
        total_score = ref_score + amount_score + date_score + description_score
        
        explanation = ScoringExplanation(
            amount_match=amount_match,
            amount_score=amount_score,
            date_delta_days=delta,
            date_score=date_score,
            description_similarity=similarity,
            description_score=description_score,
            reference_substring_match=ref_match,
            reference_in_bank_ref=in_bank_ref,
            reference_in_bank_desc=in_bank_desc,
            reference_score=ref_score,
            total_score=total_score
        )
        
        return total_score, explanation

    def find_candidates(self, bank_tx: BankTransaction, admin_entries: List[AdminEntry], top_n: int = 5) -> List[MatchCandidate]:
        candidates = []
        for admin_entry in admin_entries:
            score, explanation = self.score(bank_tx, admin_entry)
            if score >= self.config.min_suggestion_threshold:
                candidates.append(MatchCandidate(
                    bank_transaction_id=str(bank_tx.id),
                    admin_entry_id=str(admin_entry.id),
                    score=score,
                    explanation=explanation
                ))
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_n]
