
from pathlib import Path
import pandas as pd

data_path = Path("data/EduPro_Online_Platform.xlsx")
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

courses = pd.read_excel(data_path, sheet_name="Courses")
transactions = pd.read_excel(data_path, sheet_name="Transactions")

transactions["TransactionDate"] = pd.to_datetime(
    transactions["TransactionDate"], errors="coerce"
)
transactions["Amount"] = pd.to_numeric(
    transactions["Amount"], errors="coerce"
)

# Check whether course type agrees with transaction amount.
check = transactions.merge(
    courses[["CourseID", "CourseType", "CoursePrice"]],
    on="CourseID",
    how="left",
    validate="many_to_one"
)

print("Transactions with missing course match:",
      check["CourseType"].isna().sum())

print("\nAmount totals by course type:")
print(check.groupby("CourseType").agg(
    transactions=("TransactionID", "count"),
    zero_amount=("Amount", lambda x: (x == 0).sum()),
    positive_amount=("Amount", lambda x: (x > 0).sum()),
    recorded_revenue=("Amount", "sum")
).to_string())

# Course-level metrics from observed transactions.
course_metrics = check.groupby("CourseID").agg(
    TransactionCount=("TransactionID", "nunique"),
    RecordedRevenue=("Amount", "sum"),
    AverageTransactionAmount=("Amount", "mean"),
    FirstTransaction=("TransactionDate", "min"),
    LastTransaction=("TransactionDate", "max")
).reset_index()

course_metrics = courses.merge(
    course_metrics, on="CourseID", how="left", validate="one_to_one"
)

course_metrics["TransactionCount"] = (
    course_metrics["TransactionCount"].fillna(0).astype(int)
)
course_metrics["RecordedRevenue"] = (
    course_metrics["RecordedRevenue"].fillna(0)
)

course_metrics.to_csv(
    output_dir / "course_metrics.csv", index=False
)

monthly_metrics = (
    check.assign(Month=check["TransactionDate"].dt.to_period("M").astype(str))
    .groupby("Month", as_index=False)
    .agg(
        TransactionCount=("TransactionID", "nunique"),
        RecordedRevenue=("Amount", "sum")
    )
)

monthly_metrics.to_csv(
    output_dir / "monthly_metrics.csv", index=False
)

print("\nSaved:", output_dir / "course_metrics.csv")
print("Saved:", output_dir / "monthly_metrics.csv")
print("\nTop 10 courses by recorded revenue:")
print(
    course_metrics.sort_values("RecordedRevenue", ascending=False)[
        ["CourseName", "CourseCategory", "CourseType",
         "TransactionCount", "RecordedRevenue"]
    ].head(10).to_string(index=False)
)

print("\nTotal recorded transaction revenue:",
      round(check["Amount"].sum(), 2))
print("\nMetrics build complete.")
