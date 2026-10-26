
from pathlib import Path
import pandas as pd

file_path = Path("data/EduPro_Online_Platform.xlsx")

if not file_path.exists():
    raise FileNotFoundError(f"Workbook not found: {file_path.resolve()}")

print("=" * 60)
print("EDUPRO - DATASET VALIDATION REPORT")
print("=" * 60)

excel = pd.ExcelFile(file_path)
print("\nSheets found:", excel.sheet_names)

for sheet in excel.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet)

    print(f"\n{'-' * 60}")
    print(f"SHEET: {sheet}")
    print(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")
    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nMissing values by column:")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    print(missing.to_string() if not missing.empty else "No missing values")

    print("\nDuplicate rows:", df.duplicated().sum())

    if not df.empty:
        print("\nSample records:")
        print(df.head(3).to_string(index=False))

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
