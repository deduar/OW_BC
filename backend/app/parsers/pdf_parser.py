from typing import List
from app.models import BankTransaction

def parse_bank_pdf(file_content: bytes, filename: str, tenant_id: str, upload_id: str) -> List[BankTransaction]:
    """
    Initial PDF ingestion strategy: Defer parsing and return clear unsupported error.
    """
    raise NotImplementedError(
        f"PDF parsing for '{filename}' is not yet implemented. Please use CSV or Excel for now."
    )
