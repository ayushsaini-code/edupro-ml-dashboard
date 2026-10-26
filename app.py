from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import bg_component
import theme

ROOT = Path(__file__).parent
DATA = ROOT / "data"
METRICS = DATA / "processed"
MODELS = ROOT / "models"

st.set_page_config(
    page_title="EduPro | Analytics Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Shared design system (CSS, components, chart styling) lives in theme.py.
theme.inject_css()
# Decorative animated background (independent of data and models).
bg_component.render_background()


# ---------- Load real project metrics ----------
course_file = METRICS / "course_metrics.csv"
monthly_file = METRICS / "monthly_metrics.csv"

if not course_file.exists() or not monthly_file.exists():
    st.error(
        "Metrics files not found. Run `python build_metrics.py` first."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_metrics(course_path: str, monthly_path: str, signature: tuple):
    """Read the processed metric files. `signature` (file mtimes) busts the
    cache whenever build_metrics.py regenerates them."""
    course_df = pd.read_csv(course_path)
    monthly_df = pd.read_csv(monthly_path)

    for frame in (course_df, monthly_df):
        for column in ("RecordedRevenue", "TransactionCount"):
            frame[column] = pd.to_numeric(
                frame[column], errors="coerce"
            ).fillna(0)
    return course_df, monthly_df


courses, monthly = load_metrics(
    str(course_file),
    str(monthly_file),
    (course_file.stat().st_mtime, monthly_file.stat().st_mtime),
)


@st.cache_data(show_spinner=False)
def load_trend(workbook_path: str, mtime: float, course_ids: tuple):
    """Monthly revenue/transactions for the selected course IDs, recalculated
    from the original transactions so the filters stay accurate."""
    transactions = pd.read_excel(workbook_path, sheet_name="Transactions")
    transactions["TransactionDate"] = pd.to_datetime(
        transactions["TransactionDate"], errors="coerce"
    )
    transactions["Amount"] = pd.to_numeric(
        transactions["Amount"], errors="coerce"
    )

    trend_df = transactions[
        transactions["CourseID"].isin(course_ids)
    ].copy()
    trend_df["Month"] = (
        trend_df["TransactionDate"].dt.to_period("M").astype(str)
    )

    return trend_df.groupby("Month", as_index=False).agg(
        RecordedRevenue=("Amount", "sum"),
        TransactionCount=("TransactionID", "nunique"),
    )


# ---------- Navigation ----------
PAGES = [
    "Executive Overview",
    "Course Analysis",
    "Revenue Trends",
    "Insights & Recommendations",
    "Model Performance",
    "Prediction Studio",
    "Feature Importance",
]

NAV_ICONS = {
    "Executive Overview": "◈",
    "Course Analysis": "▦",
    "Revenue Trends": "↗",
    "Insights & Recommendations": "✦",
    "Model Performance": "◎",
    "Prediction Studio": "◆",
    "Feature Importance": "▥",
}

PAGE_DESCRIPTIONS = {
    "Executive Overview":
        "A unified view of course performance, recorded revenue and platform activity.",
    "Course Analysis":
        "Explore course-level activity, category mix and recorded revenue.",
    "Revenue Trends":
        "Understand monthly revenue patterns and transaction activity.",
    "Insights & Recommendations":
        "Turn observed platform data into clear, evidence-led decisions.",
    "Model Performance":
        "Evaluate demand and revenue models using cross-validation and held-out test metrics.",
    "Prediction Studio":
        "Explore model-based course demand and revenue estimates.",
    "Feature Importance":
        "Inspect the available evidence about which course features influence model predictions.",
}

with st.sidebar:
    theme.sidebar_brand()

    # Status reflects a real check: do the saved model files exist?
    _model_files = [MODELS / "revenue_model.joblib",
                    MODELS / "demand_model.joblib"]
    _found = sum(path.exists() for path in _model_files)
    theme.sidebar_status(
        _found == len(_model_files),
        f"{_found} of {len(_model_files)} saved pipelines found",
    )
    st.divider()

    page = st.radio(
        "WORKSPACE",
        PAGES,
        format_func=lambda name: f"{NAV_ICONS[name]}   {name}",
    )

    st.divider()
    theme.sidebar_source(
        "Verified workbook metrics", "EduPro Online Platform · 2025"
    )


# ---------- Top bar + hero ----------
theme.topbar(
    page,
    [
        "Verified workbook metrics",
        f"{monthly['Month'].min()} → {monthly['Month'].max()}",
        f"{len(courses)} courses",
    ],
)
theme.hero(page, PAGE_DESCRIPTIONS[page])

# ---------- Filters ----------
with st.container():
    theme.filter_label("FILTERS")
    f1, f2, f3 = st.columns([1.2, 1, 1])

    categories = sorted(courses["CourseCategory"].dropna().unique())
    types = sorted(courses["CourseType"].dropna().unique())

    with f1:
        selected_categories = st.multiselect(
            "Course category",
            categories,
            default=categories,
        )

    with f2:
        selected_types = st.multiselect(
            "Course type",
            types,
            default=types,
        )

    with f3:
        sort_option = st.selectbox(
            "Rank courses by",
            ["Recorded revenue", "Transaction count", "Course rating"],
        )

filtered = courses[
    courses["CourseCategory"].isin(selected_categories)
    & courses["CourseType"].isin(selected_types)
].copy()

if filtered.empty:
    st.warning("No courses match these filters. Select another option.")
    st.stop()


# ---------- Shared column configs ----------
def _course_columns():
    return {
        "CourseName": st.column_config.TextColumn("Course", width="large"),
        "CourseCategory": st.column_config.TextColumn("Category"),
        "CourseType": st.column_config.TextColumn("Type"),
        "CourseLevel": st.column_config.TextColumn("Level"),
        "CoursePrice": st.column_config.NumberColumn(
            "Course Price", format="₹ %.2f"
        ),
        "CourseRating": st.column_config.NumberColumn(
            "Rating", format="%.2f / 5"
        ),
        "TransactionCount": st.column_config.NumberColumn(
            "Transactions", format="%d"
        ),
        "RecordedRevenue": st.column_config.NumberColumn(
            "Recorded Revenue", format="₹ %.2f"
        ),
    }


# ---------- Pages ----------
def page_executive_overview():
    total_revenue = filtered["RecordedRevenue"].sum()
    transaction_count = filtered["TransactionCount"].sum()
    course_count = len(filtered)
    average_rating = (
        filtered["CourseRating"].mean()
        if "CourseRating" in filtered.columns else float("nan")
    )

    theme.kpi_row([
        ("Recorded revenue", f"₹ {total_revenue:,.2f}",
         "Sum of transaction Amount"),
        ("Transactions", f"{transaction_count:,.0f}",
         "Transaction count, not unique users"),
        ("Courses in view", f"{course_count:,}",
         "After applying filters"),
        ("Average course rating",
         f"{average_rating:.2f}" if pd.notna(average_rating) else "N/A",
         "Average catalogue rating"),
    ])

    theme.section(
        "Platform performance",
        "Course revenue and activity from the original workbook.",
    )

    left, right = st.columns(2)

    with left:
        category_data = (
            filtered.groupby("CourseCategory", as_index=False)
            .agg(RecordedRevenue=("RecordedRevenue", "sum"))
            .sort_values("RecordedRevenue", ascending=True)
        )

        fig = px.bar(
            category_data,
            x="RecordedRevenue",
            y="CourseCategory",
            orientation="h",
            color="RecordedRevenue",
            color_continuous_scale=["#1e3a8a", theme.BLUE, theme.CYAN],
        )
        fig.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_title="Recorded revenue",
            yaxis_title="",
            bargap=0.28,
        )
        fig.update_traces(
            hovertemplate="%{y}<br>₹ %{x:,.2f}<extra></extra>"
        )
        theme.style_fig(
            fig, "Recorded revenue by category", height=400, grid="x"
        )
        theme.show_chart(fig)

    with right:
        type_data = (
            filtered.groupby("CourseType", as_index=False)
            .agg(RecordedRevenue=("RecordedRevenue", "sum"))
        )

        fig = px.pie(
            type_data,
            names="CourseType",
            values="RecordedRevenue",
            hole=0.68,
            color="CourseType",
            color_discrete_map={"Paid": theme.BLUE, "Free": theme.VIOLET},
        )
        fig.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="#0b1020", width=3)),
        )
        fig.add_annotation(
            text=f"₹ {total_revenue:,.0f}<br><span style='font-size:11px;"
                 "color:#8f9bb8'>recorded revenue</span>",
            showarrow=False,
            font=dict(size=18, color="#ffffff"),
        )
        theme.style_fig(
            fig, "Recorded revenue mix by course type", height=400
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.12,
                xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=20, r=20, t=64, b=30),
        )
        theme.show_chart(fig)

    theme.section(
        "Top-performing courses",
        "Ranked by observed transaction revenue.",
    )

    top_courses = filtered.nlargest(8, "RecordedRevenue")[
        ["CourseName", "CourseCategory", "CourseType",
         "TransactionCount", "RecordedRevenue", "CourseRating"]
    ].copy()
    top_courses["RecordedRevenue"] = top_courses["RecordedRevenue"].round(2)

    columns = _course_columns()
    theme.show_table(
        top_courses,
        height=350,
        column_config={
            key: columns[key] for key in top_courses.columns
        },
    )


def page_course_analysis():
    theme.section(
        "Course portfolio",
        "Compare course-level transaction volume and recorded revenue.",
    )

    if sort_option == "Recorded revenue":
        sort_column = "RecordedRevenue"
    elif sort_option == "Transaction count":
        sort_column = "TransactionCount"
    else:
        sort_column = "CourseRating"

    ranked = filtered.sort_values(sort_column, ascending=False)

    fig = px.scatter(
        filtered,
        x="TransactionCount",
        y="RecordedRevenue",
        color="CourseCategory",
        size="CourseRating",
        size_max=22,
        opacity=0.85,
        hover_name="CourseName",
        hover_data=["CourseType", "CoursePrice", "CourseLevel"],
        color_discrete_sequence=theme.PALETTE,
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color="rgba(255,255,255,0.35)"))
    )
    fig.update_layout(legend_title_text="Course category")
    theme.style_fig(
        fig, "Course activity vs recorded revenue",
        height=480, grid="both", legend_bottom=True,
    )
    fig.update_xaxes(title_text="Transaction count")
    fig.update_yaxes(title_text="Recorded revenue (₹)")
    theme.show_chart(fig)

    theme.section(
        "Course table", f"Ranked by {sort_option.lower()}."
    )

    display_cols = [
        "CourseName", "CourseCategory", "CourseType", "CourseLevel",
        "CoursePrice", "CourseRating", "TransactionCount", "RecordedRevenue",
    ]
    columns = _course_columns()
    theme.show_table(
        ranked[display_cols].round(2),
        height=450,
        column_config={key: columns[key] for key in display_cols},
    )

    theme.stretch(
        st.download_button,
        "Download filtered course metrics",
        data=ranked.to_csv(index=False).encode("utf-8"),
        file_name="edupro_filtered_course_metrics.csv",
        mime="text/csv",
    )


def page_revenue_trends():
    theme.section(
        "Monthly revenue",
        "Observed transaction revenue by calendar month.",
    )

    workbook = DATA / "EduPro_Online_Platform.xlsx"

    if selected_types and selected_categories and workbook.exists():
        trend = load_trend(
            str(workbook),
            workbook.stat().st_mtime,
            tuple(filtered["CourseID"].tolist()),
        )
    else:
        trend = monthly.copy()
        if not workbook.exists():
            st.warning(
                "Original workbook not found; showing unfiltered monthly "
                "metrics."
            )

    if trend.empty:
        st.info("No transactions are recorded for the selected courses.")
        return

    peak = trend.loc[trend["RecordedRevenue"].idxmax()]
    theme.kpi_row([
        ("Recorded revenue", f"₹ {trend['RecordedRevenue'].sum():,.2f}",
         "Sum across months in view"),
        ("Transactions", f"{trend['TransactionCount'].sum():,.0f}",
         "Transaction count, not unique users"),
        ("Peak revenue month", str(peak["Month"]),
         f"₹ {peak['RecordedRevenue']:,.2f} recorded"),
        ("Average monthly revenue",
         f"₹ {trend['RecordedRevenue'].mean():,.2f}",
         f"Across {len(trend)} months"),
    ])

    st.write("")

    fig = px.line(
        trend,
        x="Month",
        y="RecordedRevenue",
        markers=True,
        color_discrete_sequence=[theme.CYAN],
    )
    fig.update_traces(
        line=dict(width=3, shape="spline", smoothing=0.6),
        marker=dict(size=8, line=dict(width=2, color="#0b1020")),
        fill="tozeroy",
        fillcolor="rgba(34,211,238,0.10)",
        hovertemplate="%{x}<br>₹ %{y:,.2f}<extra></extra>",
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Recorded revenue (₹)",
        hovermode="x unified",
    )
    theme.style_fig(fig, "Monthly recorded revenue", height=400)
    fig.update_yaxes(tickprefix="₹ ")
    theme.show_chart(fig)

    fig2 = px.bar(
        trend,
        x="Month",
        y="TransactionCount",
        color="TransactionCount",
        color_continuous_scale=["#1e3a8a", theme.BLUE, theme.VIOLET],
    )
    fig2.update_layout(
        coloraxis_showscale=False,
        xaxis_title="Month",
        yaxis_title="Transactions",
        hovermode="x unified",
        bargap=0.3,
    )
    theme.style_fig(fig2, "Transactions by month", height=360)
    theme.show_chart(fig2)

    theme.section("Monthly detail")
    theme.show_table(
        trend,
        height=350,
        column_config={
            "Month": st.column_config.TextColumn("Month"),
            "RecordedRevenue": st.column_config.NumberColumn(
                "Recorded Revenue", format="₹ %.2f"
            ),
            "TransactionCount": st.column_config.NumberColumn(
                "Transactions", format="%d"
            ),
        },
    )


def page_insights():
    total = filtered["RecordedRevenue"].sum()
    paid = filtered.loc[
        filtered["CourseType"] == "Paid", "RecordedRevenue"
    ].sum()
    free = filtered.loc[
        filtered["CourseType"] == "Free", "RecordedRevenue"
    ].sum()

    best = filtered.sort_values("RecordedRevenue", ascending=False).head(1)

    theme.section(
        "Observed insights",
        "These statements are calculated from recorded data, not forecasts.",
    )

    c1, c2 = st.columns(2, gap="large")

    with c1:
        if total > 0:
            theme.render(theme.kpi_html(
                "Revenue contribution · paid courses",
                f"{paid / total:.1%}",
                "Share of recorded revenue attributed to paid courses "
                "in the current filtered view.",
                accent="blue",
            ))
        else:
            theme.render(theme.kpi_html(
                "Revenue contribution · paid courses",
                "N/A",
                "No recorded revenue is present in this filtered view.",
                accent="blue",
            ))

        st.write("")
        theme.render(theme.kpi_html(
            "Recorded revenue · free courses",
            f"₹ {free:,.2f}",
            "Transaction amounts only; indirect value is not measured.",
            accent="violet",
        ))

    with c2:
        if not best.empty:
            row = best.iloc[0]
            theme.render(theme.kpi_html(
                "Top course by recorded revenue",
                row["CourseName"],
                [
                    f"Category: {row['CourseCategory']}",
                    f"Recorded revenue: ₹ {row['RecordedRevenue']:,.2f}",
                    f"Transactions: {row['TransactionCount']:.0f}",
                ],
                accent="cyan",
                small=True,
            ))

    theme.callout(
        "info",
        "Recommendation",
        "Review high-revenue courses alongside ratings, pricing and "
        "transaction volume before changing budgets or prices. "
        "These descriptive results are not causal evidence.",
    )


# ---------- Router ----------
if page == "Executive Overview":
    page_executive_overview()

elif page == "Course Analysis":
    page_course_analysis()

elif page == "Revenue Trends":
    page_revenue_trends()

elif page == "Insights & Recommendations":
    page_insights()

# ---------- Machine Learning pages ----------
elif page == "Model Performance":
    from ml_pages import show_model_performance
    show_model_performance()

elif page == "Prediction Studio":
    from ml_pages import show_prediction_studio
    show_prediction_studio()

elif page == "Feature Importance":
    from ml_pages import show_feature_importance
    show_feature_importance()

# ---------- Footer ----------
theme.footer(
    "EDUPRO ANALYTICS STUDIO · Recorded data is descriptive, "
    "not a machine-learning forecast."
)
