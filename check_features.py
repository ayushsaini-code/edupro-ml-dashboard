
from pathlib import Path
import pandas as pd

path = (
    Path(__file__).parent
    / "data"
    / "processed"
    / "forecast_training_dataset.csv"
)

df = pd.read_csv(path)

cols = [
    "CoursePrice",
    "HistoricalAverageAmount",
    "HistoricalRevenue",
    "HistoricalTransactions",
    "FutureRevenue",
]

print("Feature correlation with future revenue:")
print(df[cols].corr()["FutureRevenue"].round(3))

print("\nPrice vs historical average amount:")
print(
    df[["CoursePrice", "HistoricalAverageAmount"]]
    .describe()
    .round(2)
)

print("\nSample rows:")
print(df[cols].head(10).to_string(index=False))


from pathlib import Path
import pandas as pd

base = Path(__file__).parent
file_path = base / "data" / "EduPro_Online_Platform.xlsx"

courses = pd.read_excel(file_path, sheet_name="Courses")
transactions = pd.read_excel(file_path, sheet_name="Transactions")

transactions["Amount"] = pd.to_numeric(
    transactions["Amount"], errors="coerce"
)

print("\n--- COURSE PRICE DISTRIBUTION ---")
print(courses["CoursePrice"].describe())
print("Free courses:", (courses["CoursePrice"] == 0).sum())
print("Paid courses:", (courses["CoursePrice"] > 0).sum())

print("\n--- TRANSACTION AMOUNT DISTRIBUTION ---")
print(transactions["Amount"].describe())
print("Zero-amount transactions:", (transactions["Amount"] == 0).sum())
print("Positive-amount transactions:", (transactions["Amount"] > 0).sum())

print("\n--- PRICE VS TRANSACTION AMOUNT ---")
check = transactions.merge(
    courses[["CourseID", "CoursePrice"]],
    on="CourseID",
    how="left"
)

check["AmountMatchesPrice"] = (
    (check["Amount"] - check["CoursePrice"]).abs() < 0.01
)

print("Transactions matching course price:")
print(check["AmountMatchesPrice"].value_counts(dropna=False))

print("\n--- SAMPLE PAID-COURSE TRANSACTIONS ---")
print(
    check.loc[
        check["CoursePrice"] > 0,
        ["CourseID", "CoursePrice", "Amount"]
    ].head(15).to_string(index=False)
)

processed_path = (
    Path(__file__).parent
    / "data"
    / "processed"
    / "forecast_training_dataset.csv"
)

df = pd.read_csv(processed_path)

print("\n--- COURSE-LEVEL TARGET CHECK ---")
print(
    df.groupby(df["CoursePrice"] > 0)
    [["HistoricalTransactions", "FutureRevenue"]]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

print("\n--- FUTURE REVENUE AND PRICE CHECK ---")
print(
    df[["CoursePrice", "FutureRevenue"]]
    .sort_values("CoursePrice", ascending=False)
    .head(15)
    .to_string(index=False)
)

print("\n--- PAID COURSES WITH ZERO FUTURE REVENUE ---")
print(
    df.loc[
        (df["CoursePrice"] > 0) & (df["FutureRevenue"] == 0),
        ["CoursePrice", "HistoricalTransactions", "FutureRevenue"]
    ].to_string(index=False)
)

print("\n--- FUTURE TRANSACTION DISTRIBUTION ---")
print(df["FutureTransactions"].describe().round(2))

print("\n--- FUTURE TRANSACTIONS BY COURSE TYPE ---")
print(
    df.groupby(df["CoursePrice"] > 0)["FutureTransactions"]
    .agg(["count", "mean", "std", "min", "max"])
    .round(2)
)

print("\n--- ZERO FUTURE TRANSACTION COURSES ---")
print("Count:", (df["FutureTransactions"] == 0).sum())

print("\n--- TARGET RELATIONSHIP ---")
print(
    df[["FutureTransactions", "FutureRevenue", "CoursePrice"]]
    .corr()
    .round(3)
)

print("\n--- DEMAND MODEL PREDICTIONS ---")

pred_path = (
    Path(__file__).parent
    / "reports"
    / "holdout_predictions.csv"
)

pred = pd.read_csv(pred_path)
print("Columns:", pred.columns.tolist())
print(pred.head(10).to_string(index=False))

print("\n--- DEMAND METRICS ---")
metrics_path = (
    Path(__file__).parent
    / "reports"
    / "model_metrics.csv"
)

metrics = pd.read_csv(metrics_path)
print(
    metrics.loc[
        metrics["Target"].astype(str).str.lower().str.contains("demand|transaction")
    ].to_string(index=False)
)
