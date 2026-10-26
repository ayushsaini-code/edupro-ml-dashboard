
import pandas as pd

file_path = "data/EduPro_Online_Platform.xlsx"

courses = pd.read_excel(file_path, sheet_name="Courses")
transactions = pd.read_excel(file_path, sheet_name="Transactions")

transactions["TransactionDate"] = pd.to_datetime(
    transactions["TransactionDate"], errors="coerce"
)

print("\n===== DATE RANGE =====")
print("First transaction:", transactions["TransactionDate"].min())
print("Last transaction:", transactions["TransactionDate"].max())

print("\n===== TRANSACTION AMOUNT =====")
print(transactions["Amount"].describe())
print("Zero-amount transactions:", (transactions["Amount"] == 0).sum())
print("Positive-amount transactions:", (transactions["Amount"] > 0).sum())
print("Negative-amount transactions:", (transactions["Amount"] < 0).sum())

print("\n===== COURSE TYPE =====")
print(courses["CourseType"].value_counts(dropna=False))

print("\n===== COURSE CATEGORIES =====")
print(courses["CourseCategory"].value_counts(dropna=False))

print("\n===== COURSE LEVELS =====")
print(courses["CourseLevel"].value_counts(dropna=False))

print("\n===== TRANSACTIONS PER COURSE =====")
counts = transactions.groupby("CourseID").size()
print(counts.describe())
print("Unique course IDs in transactions:", transactions["CourseID"].nunique())
print("Course IDs in transactions missing from catalogue:",
      len(set(transactions["CourseID"]) - set(courses["CourseID"])))

print("\n===== MONTHLY TRANSACTION COUNTS =====")
print(
    transactions.dropna(subset=["TransactionDate"])
    .assign(Month=lambda d: d["TransactionDate"].dt.to_period("M").astype(str))
    .groupby("Month").size().to_string()
)

print("\n===== ANALYSIS COMPLETE =====")
