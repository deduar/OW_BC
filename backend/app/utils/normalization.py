import re
from datetime import datetime

def parse_es_amount(amount_str: str) -> float:
    """
    Parses an ES-style amount string:
    - Thousands separator: .
    - Decimal separator: ,
    - Example: 1.234,56 -> 1234.56
    - Example: -25.973,02 -> -25973.02
    """
    if not amount_str:
        return 0.0
    
    # Remove thousands separator (.)
    # Replace decimal separator (,) with (.)
    normalized = amount_str.replace(".", "").replace(",", ".")
    
    # Remove any character that is not a digit, dot, or minus sign
    normalized = re.sub(r"[^\d.-]", "", normalized)
    
    try:
        return float(normalized)
    except ValueError:
        return 0.0

def parse_date(date_str: str) -> datetime:
    """
    Parses dates in formats:
    - DD/MM/YYYY
    - DD-MM-YYYY
    """
    if not date_str:
        raise ValueError("Empty date string")
    
    formats = ["%d/%m/%Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unsupported date format: {date_str}")

def normalize_description(description: str) -> str:
    """
    Cleans and normalizes bank descriptions to improve matching.
    Example: "MP *MERCADONA" -> "MERCADONA"
    """
    if not description:
        return ""
        
    # Lowercase
    normalized = description.lower()
    
    # Remove common prefixes/noise
    prefixes = ["mp *", "tpbw ", "cr.i/rec ", "cr.i/ob ", "com. ", "trf.mb ", "trf.ob ", "pago movil cce ", "banesco pago movil ", "pago tdc c/c en cuenta"]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            
    # Remove leading numbers/codes (e.g., "0191 ")
    normalized = re.sub(r"^\d{4,}\s+", "", normalized)
    
    # Remove multiple spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    return normalized

def normalize_reference(reference: str) -> str:
    """
    Normalizes a reference token to digits-only for substring matching.
    """
    if not reference:
        return ""
    return re.sub(r"\D", "", reference)
