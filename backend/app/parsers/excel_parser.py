import io
import json
import xlrd
import openpyxl
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
from app.utils.normalization import parse_es_amount, parse_date
from app.models import BankTransaction

def parse_bank_excel(file_content: bytes, filename: str, tenant_id: str, upload_id: str) -> List[BankTransaction]:
    """
    Parses an Excel bank statement (.xls or .xlsx).
    Handles real XLS, HTML-masked XLS, and XLSX.
    """
    transactions = []
    
    if filename.lower().endswith(".xlsx"):
        transactions = _parse_xlsx(file_content, tenant_id, upload_id)
    elif filename.lower().endswith(".xls"):
        try:
            transactions = _parse_xls_real(file_content, tenant_id, upload_id)
        except Exception:
            # Fallback to HTML parsing for XLS files that are actually HTML
            try:
                transactions = _parse_xls_html(file_content, tenant_id, upload_id)
            except Exception as e:
                raise ValueError(f"Could not parse XLS file: {e}")
    else:
        raise ValueError(f"Unsupported file extension: {filename}")
        
    return transactions

def _parse_xlsx(file_content: bytes, tenant_id: str, upload_id: str) -> List[BankTransaction]:
    wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
    sheet = wb.active
    
    rows = list(sheet.rows)
    if not rows:
        return []
        
    # Find header row
    header_idx = -1
    for i, row in enumerate(rows):
        values = [str(cell.value).strip().lower() if cell.value else "" for cell in row]
        if any(v in ["fecha", "monto", "importe"] for v in values):
            header_idx = i
            break
            
    if header_idx == -1:
        raise ValueError("Could not find header row in XLSX")
        
    headers = [str(cell.value).strip().lower() if cell.value else "" for cell in rows[header_idx]]
    
    transactions = []
    for i in range(header_idx + 1, len(rows)):
        row_cells = rows[i]
        row_dict = {headers[j]: cell.value for j, cell in enumerate(row_cells) if j < len(headers)}
        
        try:
            trans = _map_row_to_transaction(row_dict, tenant_id, upload_id)
            if trans:
                transactions.append(trans)
        except Exception:
            continue
            
    return transactions

def _parse_xls_real(file_content: bytes, tenant_id: str, upload_id: str) -> List[BankTransaction]:
    wb = xlrd.open_workbook(file_contents=file_content)
    sheet = wb.sheet_by_index(0)
    
    if sheet.nrows == 0:
        return []
        
    header_idx = -1
    for i in range(sheet.nrows):
        values = [str(sheet.cell_value(i, j)).strip().lower() for j in range(sheet.ncols)]
        if any(v in ["fecha", "monto", "importe"] for v in values):
            header_idx = i
            break
            
    if header_idx == -1:
        raise ValueError("Could not find header row in XLS")
        
    headers = [str(sheet.cell_value(header_idx, j)).strip().lower() for j in range(sheet.ncols)]
    
    transactions = []
    for i in range(header_idx + 1, sheet.nrows):
        row_dict = {headers[j]: sheet.cell_value(i, j) for j in range(sheet.ncols) if j < len(headers)}
        try:
            trans = _map_row_to_transaction(row_dict, tenant_id, upload_id)
            if trans:
                transactions.append(trans)
        except Exception:
            continue
            
    return transactions

def _parse_xls_html(file_content: bytes, tenant_id: str, upload_id: str) -> List[BankTransaction]:
    soup = BeautifulSoup(file_content, "lxml")
    table = soup.find("table")
    if not table:
        raise ValueError("No table found in HTML-XLS")
        
    rows = table.find_all("tr")
    if not rows:
        return []
        
    # Find header
    header_row = rows[0]
    headers = [th.get_text().strip().lower() for th in header_row.find_all(["td", "th"])]
    
    transactions = []
    for i in range(1, len(rows)):
        cols = rows[i].find_all("td")
        if len(cols) < len(headers):
            continue
            
        row_dict = {headers[j]: cols[j].get_text().strip() for j in range(len(headers))}
        try:
            trans = _map_row_to_transaction(row_dict, tenant_id, upload_id)
            if trans:
                transactions.append(trans)
        except Exception:
            continue
            
    return transactions

def _map_row_to_transaction(row_dict: dict, tenant_id: str, upload_id: str) -> Optional[BankTransaction]:
    # Common mappings
    # Fecha: fecha, date
    # Amount: importe, monto, amount, value
    # Description: descripción, descripcion, description, details, concepto
    # Reference: referencia, reference, ref
    
    date_val = row_dict.get("fecha") or row_dict.get("date")
    if not date_val:
        return None
        
    if isinstance(date_val, datetime):
        date = date_val
    elif isinstance(date_val, str):
        # Handle YYYY/MM/DD seen in Banesco HTML
        if "/" in date_val and len(date_val.split("/")[0]) == 4:
            date = datetime.strptime(date_val, "%Y/%m/%d")
        else:
            date = parse_date(date_val)
    else:
        # Excel date (float)
        try:
            # We don't have wb here to use xldate_as_tuple for XLS
            # But for XLSX openpyxl already returns datetime if cell type is date
            return None
        except Exception:
            return None
            
    amount_val = row_dict.get("importe") or row_dict.get("monto") or row_dict.get("amount") or row_dict.get("monto ")
    if amount_val is None:
        return None
        
    if isinstance(amount_val, (int, float)):
        amount = float(amount_val)
    else:
        amount = parse_es_amount(str(amount_val))
        
    description = str(row_dict.get("descripción") or row_dict.get("descripcion") or row_dict.get("description") or "").strip()
    reference = str(row_dict.get("referencia") or row_dict.get("reference") or "").strip()
    
    return BankTransaction(
        tenant_id=tenant_id,
        upload_id=upload_id,
        date=date,
        amount=amount,
        description=description,
        reference_raw=reference,
        raw_row_json=json.dumps({str(k): str(v) for k, v in row_dict.items()})
    )
