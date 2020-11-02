import arcpy
import pandas as pd
import os

excel_file = r"C:\Users\LENOVO\PycharmProjects\mapit\domaintools\hs_domainlist.xlsx"  # arcpy.GetParameterAsText(0)
gdb = r"C:\Users\LENOVO\PycharmProjects\mapit\domaintools\domain_tables.gdb"  # arcpy.GetParameterAsText(1)


df = pd.read_excel(excel_file)
sheets = df.sheet_names

for sheet in sheets:
    sheet = str(sheet).encode('utf-8')
    table_out = os.path.join(gdb, sheet)
    arcpy.ExcelToTable_conversion(excel_file, table_out, sheet)
