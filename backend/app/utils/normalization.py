import re
from datetime import datetime

def parse_es_amount(amount_str: str) -> float:
    """
    Parses an amount string, handling both:
    - ES-style: 1.234,56 -> 1234.56 (dot = thousands, comma = decimal)
    - Standard: 2530.74 -> 2530.74 (dot = decimal)
    """
    if not amount_str:
        return 0.0
    
    s = str(amount_str).strip()
    
    # Check if it's Spanish format (has both comma for decimal and dot for thousands)
    # e.g., "1.234,56" -> Spanish format
    if ',' in s and '.' in s and s.rfind(',') > s.rfind('.'):
        # Spanish format: remove dots (thousands), replace comma with dot (decimal)
        normalized = s.replace(".", "").replace(",", ".")
    elif ',' in s:
        # Only comma, assume Spanish decimal: 1234,56 -> 1234.56
        normalized = s.replace(",", ".")
    elif '.' in s:
        # Only dot - check if it's standard format (2 decimal digits after dot)
        # or Spanish format (thousands separator)
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Standard format: 2530.74 -> 2530.74
            normalized = s
        else:
            # Spanish format: 1.234 -> 1234
            normalized = s.replace(".", "")
    else:
        # No dots or commas, just a number
        normalized = s
    
    # Remove any character that is not a digit, dot, or minus sign
    normalized = re.sub(r"[^\d.-]", "", normalized)
    
    try:
        return float(normalized)
    except ValueError:
        return 0.0

def parse_date(date_str: str) -> datetime:
    """
    Parses dates in formats:
    - YYYY-MM-DD (ISO format)
    - DD/MM/YYYY
    - DD-MM-YYYY
    """
    if not date_str:
        raise ValueError("Empty date string")
    
    date_str = str(date_str).strip()
    
    # Try ISO format first (YYYY-MM-DD)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    # Try DD/MM/YYYY and DD-MM-YYYY
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
