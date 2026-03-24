from typing import Iterator
from app.parsers.csv_parser import normalize_description


def parse_html_bank_statement(content: bytes, filename: str) -> Iterator[dict]:
    from html.parser import HTMLParser
    import re
    
    class TableParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_table = False
            self.in_row = False
            self.in_cell = False
            self.current_row = []
            self.current_cell = ""
            self.rows = []
            self.in_body = False
        
        def handle_starttag(self, tag, attrs):
            if tag == "table":
                self.in_table = True
            elif tag == "tbody":
                self.in_body = True
            elif tag == "tr" and self.in_table:
                self.in_row = True
                self.current_row = []
            elif tag in ("td", "th") and self.in_row:
                self.in_cell = True
                self.current_cell = ""
        
        def handle_endtag(self, tag):
            if tag == "table":
                self.in_table = False
                self.in_body = False
            elif tag == "tbody":
                self.in_body = False
            elif tag in ("td", "th") and self.in_cell:
                self.in_cell = False
                self.current_row.append(self.current_cell.strip())
            elif tag == "tr" and self.in_row:
                self.in_row = False
                if self.current_row:
                    self.rows.append(self.current_row)
        
        def handle_data(self, data):
            if self.in_cell:
                self.current_cell += data
    
    html_content = content.decode("utf-8", errors="replace")
    parser = TableParser()
    try:
        parser.feed(html_content)
    except:
        pass
    
    rows = parser.rows
    
    if len(rows) < 2:
        return
    
    headers = [h.lower().strip() for h in rows[0]]
    
    date_col = next((i for i, h in enumerate(headers) if "fecha" in h or "date" in h), 0)
    desc_col = next((i for i, h in enumerate(headers) if "descripcion" in h or "detalle" in h or "concepto" in h or "description" in h or "reference" in h or "referencia" in h), 1)
    amount_col = next((i for i, h in enumerate(headers) if "monto" in h or "importe" in h or "amount" in h or "valor" in h or "credito" in h or "debito" in h), 2)
    ref_col = next((i for i, h in enumerate(headers) if "referencia" in h or "ref" in h or "referencia" in h), -1)
    
    for row in rows[1:]:
        if len(row) <= max(date_col, desc_col, amount_col):
            continue
        
        raw_date = row[date_col] if date_col < len(row) else ""
        raw_desc = row[desc_col] if desc_col < len(row) else ""
        raw_amount = row[amount_col] if amount_col < len(row) else ""
        raw_ref = row[ref_col] if ref_col >= 0 and ref_col < len(row) else ""
        
        if not raw_amount or raw_amount.strip() in ["-", "", "0", "0,00"]:
            continue
        
        yield {
            "raw_date": raw_date,
            "raw_description": raw_desc,
            "raw_amount": raw_amount,
            "raw_reference": raw_ref,
            "normalized_description": normalize_description(raw_desc),
            "source_file": filename
        }
