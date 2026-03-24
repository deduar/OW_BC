import openpyxl
wb = openpyxl.load_workbook('/app/data/example/01/pagos FuerzaMovil.xlsx', data_only=True)
sheet = wb.active
for i, row in enumerate(sheet.iter_rows(max_row=5, values_only=True)):
    print(f"Row {i}: {row}")
