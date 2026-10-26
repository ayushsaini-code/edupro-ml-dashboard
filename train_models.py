
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = DATA / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"

for folder in [OUT, MODELS, REPORTS]:
    folder.mkdir(parents=True, exist_ok=True)

workbook = DATA / "EduPro_Online_Platform.xlsx"

courses = pd.read_excel(workbook, sheet_name="Courses")
transactions = pd.read_excel(workbook, sheet_name="Transactions")

transactions["TransactionDate"] = pd.to_datetime(
    transactions["TransactionDate"], errors="coerce"
)
transactions["Amount"] = pd.to_numeric(
    transactions["Amount"], errors="coerce"
).fillna(0)

transactions = transactions.dropna(
    subset=["TransactionDate", "CourseID"]
).copy()

# Feature period: January-August 2025.
# Target period: September-December 2025.
feature_tx = transactions[
    (transactions["TransactionDate"] >= "2025-01-01")
    & (transactions["TransactionDate"] < "2025-09-01")
]

target_tx = transactions[
    (transactions["TransactionDate"] >= "2025-09-01")
    & (transactions["TransactionDate"] < "2026-01-01")
]

# Build one row per course, including courses with no transactions
# in either period.
historical = feature_tx.groupby("CourseID").agg(
    HistoricalTransactions=("TransactionID", "nunique"),
    HistoricalRevenue=("Amount", "sum"),
    HistoricalAverageAmount=("Amount", "mean"),
).reset_index()

targets = target_tx.groupby("CourseID").agg(
    FutureTransactions=("TransactionID", "nunique"),
    FutureRevenue=("Amount", "sum"),
).reset_index()

df = courses.merge(historical, on="CourseID", how="left")
df = df.merge(targets, on="CourseID", how="left")

for col in [
    "HistoricalTransactions", "HistoricalRevenue",
    "HistoricalAverageAmount", "FutureTransactions", "FutureRevenue"
]:
    df[col] = df[col].fillna(0)

# Numeric duration: workbook sample showed numeric hours.
# Invalid values are handled as missing and imputed in the pipeline.
numeric_features = [
    "CoursePrice",
    "CourseDuration",
    "CourseRating",
    "HistoricalTransactions",
    "HistoricalRevenue",
    "HistoricalAverageAmount",
]

categorical_features = [
    "CourseCategory",
    "CourseType",
    "CourseLevel",
]

for col in numeric_features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

X = df[numeric_features + categorical_features].copy()

y_targets = {
    "demand": df["FutureTransactions"].astype(float),
    "revenue": df["FutureRevenue"].astype(float),
}

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

def make_models():
    return {
        "Mean Baseline": DummyRegressor(strategy="mean"),
        "Ridge Regression": Ridge(alpha=10.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=250,
            min_samples_leaf=3,
            max_features=0.8,
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.04,
            max_depth=2,
            loss="huber",
            random_state=42,
        ),
    }

all_metrics = []
all_predictions = []
all_importance = []
selected_models = {}

# Keep the same course holdout for both targets.
indices = np.arange(len(df))
train_idx, test_idx = train_test_split(
    indices, test_size=0.20, random_state=42
)

for target_name, y in y_targets.items():
    print(f"\n{'=' * 60}")
    print(f"TRAINING TARGET: {target_name.upper()}")
    print("=" * 60)

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    candidates = []

    for model_name, estimator in make_models().items():
        pipeline = Pipeline([
            ("preprocess", preprocessor),
            ("model", estimator),
        ])

        cv_scores = cross_val_score(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring="neg_root_mean_squared_error",
            n_jobs=1,
        )
        mean_cv_rmse = float(-cv_scores.mean())

        pipeline.fit(X_train, y_train)
        predictions = np.maximum(pipeline.predict(X_test), 0)

        mae = float(mean_absolute_error(y_test, predictions))
        rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))

        if len(y_test) > 1 and y_test.nunique() > 1:
            r2 = float(r2_score(y_test, predictions))
        else:
            r2 = float("nan")

        all_metrics.append({
            "Target": target_name,
            "Model": model_name,
            "CV_RMSE": mean_cv_rmse,
            "Test_MAE": mae,
            "Test_RMSE": rmse,
            "Test_R2": r2,
        })

        candidates.append((mean_cv_rmse, model_name, pipeline))

        print(
            f"{model_name:20s} | CV RMSE: {mean_cv_rmse:.3f}"
            f" | Test MAE: {mae:.3f} | Test RMSE: {rmse:.3f}"
            f" | Test R2: {r2:.3f}"
        )

    # Select using training-fold CV only, not test-set performance.
    candidates.sort(key=lambda item: item[0])
    best_cv_rmse, best_name, best_pipeline = candidates[0]

    selected_models[target_name] = best_pipeline

    # Save the selected pipeline.
    import joblib
    joblib.dump(best_pipeline, MODELS / f"{target_name}_model.joblib")

    # Store held-out predictions for transparent review.
    test_output = df.iloc[test_idx][
        ["CourseID", "CourseName", "CourseCategory", "CourseType"]
    ].copy()
    test_output["Target"] = target_name
    test_output["Actual"] = y_test.to_numpy()
    test_output["Predicted"] = np.maximum(
        best_pipeline.predict(X_test), 0
    )
    test_output["SelectedModel"] = best_name
    all_predictions.append(test_output)

    # Permutation importance on the held-out courses.
    # Negative values can occur; importance is not causal evidence.
    try:
        importance = permutation_importance(
            best_pipeline,
            X_test,
            y_test,
            scoring="neg_root_mean_squared_error",
            n_repeats=20,
            random_state=42,
            n_jobs=1,
        )
        imp_df = pd.DataFrame({
            "Target": target_name,
            "Feature": X_test.columns,
            "Importance": importance.importances_mean,
        }).sort_values("Importance", ascending=False)
        all_importance.append(imp_df)
    except Exception as exc:
        print("Importance calculation skipped:", exc)

    print(f"\nSelected by CV: {best_name}")
    print(f"Selected CV RMSE: {best_cv_rmse:.3f}")

metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(REPORTS / "model_metrics.csv", index=False)

pd.concat(all_predictions, ignore_index=True).to_csv(
    REPORTS / "holdout_predictions.csv", index=False
)

if all_importance:
    pd.concat(all_importance, ignore_index=True).to_csv(
        REPORTS / "feature_importance.csv", index=False
    )

# Save dataset used to construct targets/features for auditability.
df.to_csv(OUT / "forecast_training_dataset.csv", index=False)

summary = {
    "feature_period": "2025-01-01 to 2025-08-31",
    "target_period": "2025-09-01 to 2025-12-31",
    "course_rows": int(len(df)),
    "train_courses": int(len(train_idx)),
    "test_courses": int(len(test_idx)),
    "target_definitions": {
        "demand": "Count of transaction records per course in target period; proxy, not verified unique enrollments.",
        "revenue": "Sum of recorded Amount per course in target period.",
    },
    "selected_models": {
        target: min(
            [m for m in all_metrics if m["Target"] == target],
            key=lambda row: row["CV_RMSE"],
        )["Model"]
        for target in y_targets
    },
    "caveat": (
        "Only 60 course observations are available. Holdout metrics may be "
        "unstable; compare with the mean baseline and avoid overclaiming."
    ),
}

with open(REPORTS / "training_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("\n" + "=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)
print("Metrics: reports/model_metrics.csv")
print("Holdout predictions: reports/holdout_predictions.csv")
print("Feature importance: reports/feature_importance.csv")
print("Saved models: models/demand_model.joblib, models/revenue_model.joblib")
print("\nSelected models:")
print(json.dumps(summary["selected_models"], indent=2))
