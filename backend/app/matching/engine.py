from typing import List, Optional, Tuple
from pydantic import BaseModel
from rapidfuzz import fuzz
from datetime import timedelta
from app.models import BankTransaction, AdminEntry
from app.utils.normalization import normalize_description, normalize_reference

class MatchConfig(BaseModel):
    date_tolerance_days: int = 2
    amount_tolerance_cents: float = 0.01  # For floating point equality
    auto_match_threshold: float = 85.0
    min_suggestion_threshold: float = 40.0
    
    # Weights (normalized to 100 total maybe, or just absolute points)
    weight_amount: float = 40.0
    weight_date: float = 20.0
    weight_description: float = 20.0
    weight_reference: float = 40.0  # Bonus for reference substring match

class ScoringExplanation(BaseModel):
    amount_match: bool
    amount_score: float
    date_delta_days: int
    date_score: float
    description_similarity: float
    description_score: float
    reference_substring_match: bool
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

    def score(self, bank_tx: BankTransaction, admin_entry: AdminEntry) -> Tuple[float, ScoringExplanation]:
        # 1. Amount match (strict for MVP)
        amount_match = abs(bank_tx.amount - admin_entry.amount) <= self.config.amount_tolerance_cents
        amount_score = self.config.weight_amount if amount_match else 0.0
        
        # 2. Date match
        delta = abs((bank_tx.date - admin_entry.date).days)
        date_score = 0.0
        if delta <= self.config.date_tolerance_days:
            # Linear decay for date score maybe? or just binary for MVP
            date_score = self.config.weight_date * (1 - (delta / (self.config.date_tolerance_days + 1)))
        
        # 3. Description similarity
        # Use normalized descriptions if available or normalize on the fly
        norm_bank = normalize_description(bank_tx.description)
        norm_admin = normalize_description(admin_entry.description)
        
        similarity = fuzz.token_sort_ratio(norm_bank, norm_admin)
        description_score = (similarity / 100.0) * self.config.weight_description
        
        # 4. Reference substring match (Task 6.7)
        # Check if admin reference (digits only) is inside bank reference or description (digits only)
        ref_score = 0.0
        ref_match = False
        
        # Admin reference digits
        admin_ref_digits = normalize_reference(admin_entry.reference_raw or "")
        if admin_ref_digits and len(admin_ref_digits) >= 4: # Min 4 digits to avoid noisy matches like "2025"
            # Bank reference and description digits
            bank_ref_digits = normalize_reference(bank_tx.reference_raw or "")
            bank_desc_digits = normalize_reference(bank_tx.description or "")
            
            if admin_ref_digits in bank_ref_digits or admin_ref_digits in bank_desc_digits:
                ref_match = True
                ref_score = self.config.weight_reference
        
        total_score = amount_score + date_score + description_score + ref_score
        # Cap score at 100 (or keep raw for internal and normalize for UI if needed)
        # Actually keeping it raw is fine as long as we know our threshold.
        
        explanation = ScoringExplanation(
            amount_match=amount_match,
            amount_score=amount_score,
            date_delta_days=delta,
            date_score=date_score,
            description_similarity=similarity,
            description_score=description_score,
            reference_substring_match=ref_match,
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
        
        # Rank by score descending
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_n]
