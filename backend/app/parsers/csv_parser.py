import csv
import io
import json
from datetime import datetime
from typing import List, Optional
from app.utils.normalization import parse_es_amount, parse_date
from app.models import BankTransaction

def parse_bank_csv(file_content: bytes, tenant_id: str, upload_id: str) -> List[BankTransaction]:
    """
    Parses a CSV bank statement with ; delimiter and ES-style numbers.
    Expected columns: Fecha;Referencia;Descripción;Importe;Saldo
    """
    # Try different encodings
    text_content = None
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            text_content = file_content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if text_content is None:
        raise ValueError("Could not decode CSV file")

    reader = csv.DictReader(io.StringIO(text_content), delimiter=";")
    
    # Normalize headers (remove BOM, lowercase, strip)
    reader.fieldnames = [name.strip().lower().replace("", "o") for name in reader.fieldnames]
    
    transactions = []
    
    # Map expected columns
    # Provincial DL: fecha;referencia;descripcion;importe;saldo
    # Banesco: fecha;referencia;descripcion;monto;saldo (maybe?)
    
    for row in reader:
        try:
            # Detect amount column (Importe or Monto)
            amount_key = "importe" if "importe" in row else ("monto" if "monto" in row else None)
            if not amount_key:
                # Try to find a column that looks like an amount if not found by name
                for k in row.keys():
                    if k and ("import" in k or "monto" in k):
                        amount_key = k
                        break
            
            if not amount_key:
                continue

            date_str = row.get("fecha", "").strip()
            if not date_str:
                continue
            
            date = parse_date(date_str)
            amount = parse_es_amount(row.get(amount_key, "0"))
            description = row.get("descripcion", row.get("descripción", "")).strip()
            reference = row.get("referencia", "").strip()
            
            # Create BankTransaction model
            transaction = BankTransaction(
                tenant_id=tenant_id,
                upload_id=upload_id,
                date=date,
                amount=amount,
                description=description,
                reference_raw=reference,
                raw_row_json=json.dumps(row)
            )
            transactions.append(transaction)
        except Exception as e:
            # Skip rows with errors for now, or log them
            print(f"Error parsing row {row}: {e}")
            continue
            
    return transactions
