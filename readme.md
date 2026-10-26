
# EduPro — Online Learning Platform Analytics

## Project Overview

EduPro is a data analytics and machine learning dashboard designed to explore course performance, recorded revenue, transaction activity, and predictive model performance for an online learning platform.

The application is built with Python and Streamlit, with interactive charts and tables for business analysis.

## Key Features

- Executive Overview with key performance indicators
- Course Analysis with course-level comparisons
- Revenue Trends over time
- Insights and Recommendations
- Model Performance comparison
- Prediction Studio for experimental predictions
- Feature Importance using permutation importance
- Interactive filters and a dark, AI-product-style analytics theme (shared design system in `theme.py`; decorative animated background in `bg_component.py`)

## Technology Stack

- Python
- Streamlit
- Pandas and NumPy
- Plotly
- Scikit-learn
- Joblib for saved models, where applicable

## Project Structure

```text
edupro_project/
├── app.py
├── ml_pages.py
├── theme.py
├── bg_component.py
├── .streamlit/config.toml
├── requirements.txt
├── README.md
├── data/
├── models/
└── reports/
```

The data, model, and report folders contain supporting files required by the application. Their exact contents depend on the project build.

## Setup and Run

1. Install a compatible Python version.
2. Open a terminal in the project root.
3. Create and activate a virtual environment.
4. Install the required packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Launch the application:

   ```bash
   python -m streamlit run app.py
   ```

6. Open the local URL displayed in the terminal.

## Model Evaluation and Limitations

Revenue prediction showed promising preliminary test performance, with an R² of approximately 0.951 on a test sample of 12 courses out of 60.

Demand prediction was less reliable: the mean-baseline model performed best in cross-validation among the models tested. Transaction records are used as a proxy for demand and should not be interpreted as confirmed student enrollments.

Prediction Studio estimates are experimental and have not been validated as forecasts for a new future period. Feature importance indicates predictive relationships, not causal effects.

## Responsible Interpretation

Results should be interpreted in the context of the available dataset, limited test sample, and target definitions. Further data collection and out-of-time validation are recommended before using predictions for business decisions.
