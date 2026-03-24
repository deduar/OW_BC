import io
import json
import openpyxl
from datetime import datetime
from typing import List, Optional
from app.utils.normalization import parse_es_amount, parse_date
from app.models import AdminEntry

def parse_admin_report_xlsx(file_content: bytes, tenant_id: str, upload_id: str) -> List[AdminEntry]:
    """
    Parses Fuerza Movil administrative report (XLSX).
    Detects header row, extracts Referencia, dates, amounts.
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
    sheet = wb.active
    
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []
        
    # Find header row (usually contains 'Referencia' and 'Fecha de Pago')
    header_idx = -1
    for i, row in enumerate(rows):
        if not row: continue
        values = [str(v).strip().lower() if v else "" for v in row]
        if "referencia" in values and ("fecha de pago" in values or "total pagado" in values):
            header_idx = i
            break
            
    if header_idx == -1:
        # Fallback to a simpler header search if needed
        raise ValueError("Could not find Fuerza Movil headers (Referencia, Fecha de Pago, Total Pagado)")
        
    headers = [str(v).strip().lower() if v else "" for v in rows[header_idx]]
    
    # Map column indices
    try:
        idx_ref = headers.index("referencia")
        idx_date = headers.index("fecha de pago")
        idx_amount = headers.index("total pagado")
        # Optional columns
        idx_client = headers.index("cliente") if "cliente" in headers else -1
        idx_bank = headers.index("banco") if "banco" in headers else -1
    except ValueError as e:
        raise ValueError(f"Missing required Fuerza Movil column: {e}")
        
    entries = []
    for i in range(header_idx + 1, len(rows)):
        row = rows[i]
        if not row or len(row) <= max(idx_ref, idx_date, idx_amount):
            continue
            
        ref_val = row[idx_ref]
        date_val = row[idx_date]
        amount_val = row[idx_amount]
        
        if ref_val is None and date_val is None and amount_val is None:
            continue
            
        try:
            # Parse date
            if isinstance(date_val, datetime):
                date = date_val
            elif isinstance(date_val, str):
                date = parse_date(date_val)
            else:
                continue
                
            # Parse amount
            if isinstance(amount_val, (int, float)):
                amount = float(amount_val)
            else:
                amount = parse_es_amount(str(amount_val))
                
            # Description
            client = str(row[idx_client]) if idx_client != -1 else ""
            bank = str(row[idx_bank]) if idx_bank != -1 else ""
            description = f"{client} ({bank})".strip()
            
            entry = AdminEntry(
                tenant_id=tenant_id,
                upload_id=upload_id,
                date=date,
                amount=amount,
                description=description,
                reference_raw=str(ref_val),
                raw_row_json=json.dumps({headers[j]: str(row[j]) for j in range(len(headers)) if j < len(row)})
            )
            entries.append(entry)
        except Exception:
            continue
            
    return entries
