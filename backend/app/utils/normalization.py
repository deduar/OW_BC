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
