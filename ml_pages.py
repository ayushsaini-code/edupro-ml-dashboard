import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import theme

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"
DATA = ROOT / "data" / "processed"
MODELS = ROOT / "models"

NUMERIC_FEATURES = [
    "CoursePrice",
    "CourseDuration",
    "CourseRating",
    "HistoricalTransactions",
    "HistoricalRevenue",
    "HistoricalAverageAmount",
]

CATEGORICAL_FEATURES = [
    "CourseCategory",
    "CourseType",
    "CourseLevel",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@st.cache_data(show_spinner=False)
def _read_csv(path_str: str, mtime: float):
    return pd.read_csv(path_str)


def load_csv(path):
    if not path.exists():
        st.error(f"Required file not found: {path.relative_to(ROOT)}")
        st.stop()
    return _read_csv(str(path), path.stat().st_mtime).copy()


@st.cache_resource(show_spinner=False)
def _read_model(path_str: str, mtime: float):
    return joblib.load(path_str)


def load_model(target):
    path = MODELS / f"{target}_model.joblib"
    if not path.exists():
        st.error(f"Saved model not found: {path.relative_to(ROOT)}")
        st.stop()
    return _read_model(str(path), path.stat().st_mtime)


def load_summary():
    """Read reports/training_summary.json if present (display-only)."""
    path = REPORTS / "training_summary.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def target_label(value):
    return "Revenue" if value == "revenue" else "Demand"


# --------------------------------------------------------------------------
# Model Performance
# --------------------------------------------------------------------------
def show_model_performance():
    metrics = load_csv(REPORTS / "model_metrics.csv")
    summary = load_summary()

    st.caption("Compare cross-validation and held-out test results.")

    target = st.selectbox(
        "Prediction target",
        ["revenue", "demand"],
        format_func=target_label,
    )

    result = metrics[metrics["Target"] == target].copy()

    if result.empty:
        st.warning("No metrics available for this target.")
        return

    result = result.sort_values("CV_RMSE").reset_index(drop=True)
    best = result.iloc[0]

    theme.kpi_row([
        ("CV-selected model", best["Model"], "Lowest cross-validation RMSE"),
        ("CV RMSE", f'{best["CV_RMSE"]:,.2f}', "Lower is better"),
        ("Test MAE", f'{best["Test_MAE"]:,.2f}', "Held-out courses"),
        ("Test R²", f'{best["Test_R2"]:.3f}', "Held-out courses"),
    ])

    test_courses = summary.get("test_courses", 12)
    course_rows = summary.get("course_rows", 60)

    if target == "demand":
        theme.callout(
            "warn",
            "Demand prediction limitation",
            "The Mean Baseline performed best in cross-validation. The "
            "tested ML models did not beat this baseline on the held-out "
            "test set. Treat demand estimates as experimental, not "
            "reliable course-level forecasts.",
        )
    else:
        theme.callout(
            "info",
            "Revenue model",
            f"{best['Model']} was the strongest revenue model by "
            "cross-validation RMSE. The held-out result is promising, "
            f"but evaluation covers only {test_courses} of {course_rows} "
            "courses, so performance may vary on new data.",
        )

    theme.section("Model comparison")

    display = result.rename(columns={
        "CV_RMSE": "CV RMSE",
        "Test_MAE": "Test MAE",
        "Test_RMSE": "Test RMSE",
        "Test_R2": "Test R²",
    })

    theme.show_table(
        display,
        height=350,
        column_config={
            "CV RMSE": st.column_config.NumberColumn(
                "CV RMSE", format="%.3f"
            ),
            "Test MAE": st.column_config.NumberColumn(
                "Test MAE", format="%.3f"
            ),
            "Test RMSE": st.column_config.NumberColumn(
                "Test RMSE", format="%.3f"
            ),
            "Test R²": st.column_config.NumberColumn(
                "Test R²", format="%.3f"
            ),
        },
    )

    # Highlight the CV-selected model; the others stay muted.
    chart_df = result.copy()
    chart_df["Role"] = np.where(
        chart_df["Model"] == best["Model"], "CV-selected", "Other models"
    )
    fig = px.bar(
        chart_df,
        x="Model",
        y="CV_RMSE",
        color="Role",
        color_discrete_map={
            "CV-selected": theme.CYAN,
            "Other models": "#3b4a78",
        },
        labels={
            "CV_RMSE": "Cross-validation RMSE",
            "Model": "Model",
        },
    )
    fig.update_layout(bargap=0.35, legend_title_text="")
    fig.update_xaxes(tickangle=-20)
    theme.style_fig(
        fig, "Cross-validation RMSE — lower is better", height=400
    )
    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, xanchor="right",
            x=1, bgcolor="rgba(0,0,0,0)",
        )
    )
    theme.show_chart(fig)

    theme.section("How to interpret these metrics")
    g1, g2, g3 = st.columns(3)
    with g1:
        theme.render(theme.glass_card(
            "CV RMSE",
            "Used to select the model; lower is better.",
        ))
    with g2:
        theme.render(theme.glass_card(
            "Test MAE",
            "Average absolute prediction error, in the target's units.",
        ))
    with g3:
        theme.render(theme.glass_card(
            "Test R²",
            "Compares the model with predicting the test-set mean; "
            "a negative value indicates worse performance than that "
            "reference.",
        ))

    theme.callout(
        "note",
        "",
        "Demand is measured as transaction-record count, not verified "
        "unique enrollments. All results are based on the existing "
        "historical split and should not be interpreted as guaranteed "
        "future accuracy.",
    )


# --------------------------------------------------------------------------
# Prediction Studio
# --------------------------------------------------------------------------
def show_prediction_studio():
    courses = load_csv(DATA / "forecast_training_dataset.csv")
    summary = load_summary()
    selected_models = summary.get("selected_models", {})

    st.caption(
        "Change course inputs to generate estimates from the saved pipelines."
    )

    course_names = courses["CourseName"].fillna("Unnamed course").tolist()
    selected_name = st.selectbox("Start with an existing course", course_names)
    selected = courses[courses["CourseName"] == selected_name].iloc[0]

    with st.form("prediction_form"):

        theme.section(
            "01 · Course profile",
            "Set the course's pricing, duration, rating and catalogue "
            "details.",
        )

        c1, c2, c3 = st.columns(3)

        price = c1.number_input(
            "Course price",
            min_value=0.0,
            value=float(max(0, selected["CoursePrice"]))
                if pd.notna(selected["CoursePrice"]) else 0.0,
            step=50.0,
        )
        duration = c2.number_input(
            "Duration (hours)",
            min_value=0.0,
            value=float(max(0, selected["CourseDuration"]))
                if pd.notna(selected["CourseDuration"]) else 1.0,
            step=1.0,
        )
        rating = c3.number_input(
            "Course rating",
            min_value=0.0,
            max_value=5.0,
            value=float(np.clip(
                selected["CourseRating"]
                if pd.notna(selected["CourseRating"]) else 0.0,
                0, 5
            )),
            step=0.1,
        )

        categories = sorted(
            courses["CourseCategory"].dropna().astype(str).unique().tolist()
        )
        levels = sorted(
            courses["CourseLevel"].dropna().astype(str).unique().tolist()
        )

        d1, d2, d3 = st.columns(3)
        category = d1.selectbox(
            "Category",
            categories,
            index=categories.index(str(selected["CourseCategory"]))
            if str(selected["CourseCategory"]) in categories else 0,
        )
        course_type = d2.selectbox(
            "Course type",
            ["Free", "Paid"],
            index=0 if str(selected["CourseType"]).lower() == "free" else 1,
        )
        level = d3.selectbox(
            "Course level",
            levels,
            index=levels.index(str(selected["CourseLevel"]))
            if str(selected["CourseLevel"]) in levels else 0,
        )

        st.divider()
        theme.section(
            "02 · Historical activity",
            "Use recorded activity from January–August 2025 as model "
            "inputs.",
        )

        c1, c2, c3 = st.columns(3)

        hist_tx = c1.number_input(
            "Historical transactions",
            min_value=0,
            value=int(max(0, selected["HistoricalTransactions"])),
            step=1,
        )
        hist_revenue = c2.number_input(
            "Historical recorded revenue",
            min_value=0.0,
            value=float(max(0, selected["HistoricalRevenue"])),
            step=100.0,
        )
        hist_avg = c3.number_input(
            "Historical average amount",
            min_value=0.0,
            value=float(max(0, selected["HistoricalAverageAmount"])),
            step=10.0,
        )

        submitted = theme.stretch(
            st.form_submit_button,
            "Generate predictions",
            type="primary",
        )

    if submitted:
        features = pd.DataFrame([{
            "CoursePrice": price,
            "CourseDuration": duration,
            "CourseRating": rating,
            "HistoricalTransactions": hist_tx,
            "HistoricalRevenue": hist_revenue,
            "HistoricalAverageAmount": hist_avg,
            "CourseCategory": category,
            "CourseType": course_type,
            "CourseLevel": level,
        }], columns=FEATURES)

        revenue_model = load_model("revenue")
        demand_model = load_model("demand")

        predicted_revenue = max(
            0.0, float(revenue_model.predict(features)[0])
        )
        predicted_demand = max(
            0.0, float(demand_model.predict(features)[0])
        )

        theme.section("03 · Estimated results")
        c1, c2 = st.columns(2, gap="large")

        revenue_name = selected_models.get("revenue")
        demand_name = selected_models.get("demand")

        with c1:
            theme.render(theme.result_html(
                "Predicted recorded revenue",
                f"₹{predicted_revenue:,.2f}",
                "Model estimate for the target period",
                badge=f"Model: {revenue_name}" if revenue_name else "",
                accent="blue",
            ))

        with c2:
            theme.render(theme.result_html(
                "Predicted transaction records",
                f"{predicted_demand:,.1f}",
                "Transaction-count proxy, not confirmed enrollments",
                badge=f"Model: {demand_name}" if demand_name else "",
                accent="cyan",
            ))

        st.write("")
        theme.render(
            '<div class="side-label">INPUTS USED</div>'
        )
        theme.chips([
            category,
            course_type,
            level,
            f"Price ₹{price:,.2f}",
            f"{duration:,.0f} hours",
            f"Rating {rating:.1f}",
            f"{hist_tx:,} historical transactions",
            f"₹{hist_revenue:,.2f} historical revenue",
            f"₹{hist_avg:,.2f} avg amount",
        ])

        if demand_name == "Mean Baseline":
            theme.callout(
                "warn",
                "About the demand estimate",
                "The saved demand model is a Mean Baseline, which predicts "
                "the same value regardless of the inputs above. Changing "
                "the course profile will not change this estimate.",
            )

        theme.callout(
            "note",
            "",
            "These estimates target Sep–Dec 2025 based on the training "
            "design. They are experimental outputs, not a validated "
            "forecast for a new future period. Demand is a transaction "
            "proxy, not confirmed enrollments.",
        )


# --------------------------------------------------------------------------
# Feature Importance
# --------------------------------------------------------------------------
def show_feature_importance():
    importance = load_csv(REPORTS / "feature_importance.csv")

    st.caption("Permutation importance computed on the held-out course set.")

    target = st.selectbox(
        "Target",
        ["revenue", "demand"],
        format_func=target_label,
        key="importance_target",
    )

    result = importance[importance["Target"] == target].copy()
    if result.empty:
        st.warning("No importance results are available for this target.")
        return

    result = result.sort_values("Importance", ascending=True)

    all_zero = bool((result["Importance"].abs() == 0).all())
    top = result.iloc[-1]
    positive_count = int((result["Importance"] > 0).sum())

    theme.kpi_row([
        ("Top feature",
         "None (all zero)" if all_zero else top["Feature"],
         "Largest permutation importance"),
        ("Top importance",
         f'{top["Importance"]:,.2f}',
         "Change in model score"),
        ("Features evaluated", f"{len(result)}", "Model input columns"),
        ("Positive importance", f"{positive_count}",
         "Features whose permutation hurt the score"),
    ], small=True)

    if all_zero:
        theme.callout(
            "warn",
            "All demand importances are zero",
            "This is consistent with the saved demand model being a "
            "Mean Baseline, which does not use its inputs. There is no "
            "feature signal to show for this target.",
        )

    fig = px.bar(
        result,
        x="Importance",
        y="Feature",
        orientation="h",
        color="Importance",
        color_continuous_scale=["#1e3a8a", theme.BLUE, theme.CYAN],
        labels={
            "Importance": "Change in model score",
            "Feature": "Input feature",
        },
    )
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Importance", thickness=10, len=0.7,
        ),
        bargap=0.3,
    )
    fig.update_xaxes(zeroline=True, zerolinecolor="rgba(148,163,205,0.45)")
    theme.style_fig(
        fig,
        "Permutation importance — higher is not always causal",
        height=440,
        grid="x",
    )
    theme.show_chart(fig)

    with st.expander("View importance values"):
        theme.show_table(
            result.sort_values("Importance", ascending=False),
            column_config={
                "Importance": st.column_config.NumberColumn(
                    "Importance", format="%.4f"
                ),
            },
        )

    theme.callout(
        "note",
        "How to read this",
        "Importance measures how model error changes when a feature is "
        "permuted. Negative values can occur. This is predictive "
        "evidence, not proof that a feature causes revenue or demand.",
    )
