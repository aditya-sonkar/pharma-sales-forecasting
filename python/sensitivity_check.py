"""
sensitivity_check.py
====================
Assesses whether the January 2017 near-zero anomaly in salesmonthly.csv
materially affects forecast accuracy.

Approach:
  - Training period : 2014-01 to 2018-12 (60 months)
  - Test period     : 2019-01 to 2019-10 (10 months, all available)
  - Forecast method : Simple seasonal naive + linear trend (Python proxy)
                      The actual project forecast uses Excel FORECAST.ETS().
                      This script estimates the sensitivity only -- it does NOT
                      replace the Excel forecast.

Two scenarios compared:
  Scenario A : Original monthly data (Jan 2017 = near-zero as in CSV)
  Scenario B : Jan 2017 excluded from training (model trained on remaining months)

Metrics reported : MAE, MAPE (per the project plan)

Raw data is NOT modified in either scenario.
Output: reports/Forecast_Evaluation.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent
PROCESSED = BASE / "data" / "processed"
REPORTS   = BASE / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# ── Load monthly summary ───────────────────────────────────────────────────────
monthly = pd.read_csv(PROCESSED / "monthly_summary.csv", parse_dates=["Date"])
monthly = monthly.sort_values("Date").reset_index(drop=True)

print()
print("=" * 60)
print("  Forecast Sensitivity Check")
print("=" * 60)
print(f"\nLoaded monthly_summary.csv: {len(monthly)} rows")
print(f"Date range: {monthly['Date'].min().date()} --> {monthly['Date'].max().date()}")

# ── Split ──────────────────────────────────────────────────────────────────────
train_full = monthly[monthly["Date"].dt.year <= 2018].copy()
# Exclude Oct 2019 as it is a partial month (daily data ends 2019-10-08)
test       = monthly[(monthly["Date"].dt.year == 2019) & (monthly["Date"].dt.month <= 9)].copy()

print(f"\nTraining (Scenario A, original): {len(train_full)} months")
print(f"Test period                     : {len(test)} months (2019 Jan-Sep)")
print(f"\nJan 2017 value in monthly CSV   : {monthly.loc[monthly['Date'].dt.to_period('M') == '2017-01', 'Total_Sales'].values[0]:.4f}")

# Scenario B: exclude Jan 2017 from training
train_excl = train_full[~((train_full["Date"].dt.year == 2017) &
                           (train_full["Date"].dt.month == 1))].copy()
print(f"Training (Scenario B, Jan-2017 excluded): {len(train_excl)} months")


# ── Forecast function: Seasonal + Trend ───────────────────────────────────────
def seasonal_trend_forecast(train: pd.DataFrame, n_periods: int,
                             forecast_start_month: int,
                             forecast_start_year: int) -> np.ndarray:
    """
    Simple seasonal-trend forecast:
    1. Compute monthly seasonal indices from training data.
    2. Fit a linear trend to the training data.
    3. Project n_periods ahead = trend value * seasonal index.

    This is a simplified proxy for Excel's FORECAST.ETS() to assess sensitivity.
    It is NOT the primary forecasting method for this project.
    """
    # Seasonal index: average sales for each month / overall mean
    train = train.copy()
    train["Month"] = train["Date"].dt.month
    overall_mean   = train["Total_Sales"].mean()
    seas_index     = train.groupby("Month")["Total_Sales"].mean() / overall_mean

    # Linear trend fit
    t    = np.arange(len(train))
    coeffs = np.polyfit(t, train["Total_Sales"].values, 1)
    slope, intercept = coeffs

    # Project forward
    forecasts = []
    for i in range(n_periods):
        t_fwd  = len(train) + i
        month  = ((forecast_start_month - 1 + i) % 12) + 1
        trend  = slope * t_fwd + intercept
        seas   = seas_index.get(month, 1.0)
        forecasts.append(max(0.0, trend * seas))

    return np.array(forecasts)


# ── Run both scenarios ─────────────────────────────────────────────────────────
n        = len(test)
start_m  = int(test["Date"].dt.month.iloc[0])
start_y  = int(test["Date"].dt.year.iloc[0])
actual   = test["Total_Sales"].values

fc_A = seasonal_trend_forecast(train_full, n, start_m, start_y)
fc_B = seasonal_trend_forecast(train_excl, n, start_m, start_y)


# ── Metrics ───────────────────────────────────────────────────────────────────
def mae(actual, forecast):
    return float(np.mean(np.abs(actual - forecast)))

def mape(actual, forecast):
    # Exclude months where actual is zero or near-zero to avoid division issues
    mask = actual > 1.0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - forecast[mask]) / actual[mask])) * 100)


mae_A  = mae(actual, fc_A)
mae_B  = mae(actual, fc_B)
mape_A = mape(actual, fc_A)
mape_B = mape(actual, fc_B)

mae_diff  = abs(mae_A - mae_B)
mape_diff = abs(mape_A - mape_B) if not (np.isnan(mape_A) or np.isnan(mape_B)) else float("nan")

print()
print("=" * 60)
print("  Sensitivity Results")
print("=" * 60)
print(f"\n  {'Metric':<30} {'Scenario A (original)':>22} {'Scenario B (Jan-2017 excl.)':>28}")
print(f"  {'-'*80}")
print(f"  {'MAE':<30} {mae_A:>22.2f} {mae_B:>28.2f}")
print(f"  {'MAPE':<30} {mape_A:>21.2f}% {mape_B:>27.2f}%")
print(f"\n  MAE  difference  (A vs B) : {mae_diff:.2f}")
print(f"  MAPE difference  (A vs B) : {mape_diff:.2f}%")

# Materiality assessment
avg_monthly = monthly["Total_Sales"].mean()
pct_of_avg  = (mae_diff / avg_monthly) * 100

print(f"\n  Average monthly sales (full dataset): {avg_monthly:,.1f}")
print(f"  MAE difference as % of avg monthly  : {pct_of_avg:.2f}%")

print()
print("  Interpretation:")
if pct_of_avg < 2.0:
    print("  The MAE difference between the two scenarios is less than 2% of")
    print("  average monthly sales. The 2017-01 anomaly does NOT materially")
    print("  affect forecast accuracy in this sensitivity check.")
    print("  Recommendation: Continue with original salesmonthly.csv data.")
    impact = "NOT MATERIAL (<2% of avg monthly sales)"
elif pct_of_avg < 5.0:
    print("  The MAE difference is between 2-5% of average monthly sales.")
    print("  Impact is modest. Recommend documenting the anomaly in the")
    print("  Executive Summary and noting it as a limitation.")
    impact = "MODEST (2-5% of avg monthly sales)"
else:
    print("  The MAE difference exceeds 5% of average monthly sales.")
    print("  The 2017-01 anomaly materially affects forecast results.")
    print("  Recommend explicitly discussing this in the Executive Summary.")
    print("  Consider noting this limitation in the forecasting section.")
    impact = "MATERIAL (>5% of avg monthly sales)"

print(f"\n  Impact classification: {impact}")

# ── Month-by-month comparison ─────────────────────────────────────────────────
print()
print("=" * 60)
print("  Month-by-Month Forecast Comparison (2019)")
print("=" * 60)
print(f"\n  {'Period':<10} {'Actual':>10} {'Forecast A':>12} {'Err A':>10} {'Forecast B':>12} {'Err B':>10}")
print(f"  {'-'*66}")
for i, row in enumerate(test.itertuples()):
    ym   = row.Year_Month
    act  = actual[i]
    fa   = fc_A[i]
    fb   = fc_B[i]
    print(f"  {ym:<10} {act:>10.1f} {fa:>12.1f} {fa-act:>+10.1f} {fb:>12.1f} {fb-act:>+10.1f}")

# ── Export ────────────────────────────────────────────────────────────────────
eval_df = pd.DataFrame({
    "Period":       test["Year_Month"].values,
    "Actual":       actual,
    "Forecast_A_original":  fc_A,
    "Error_A":      fc_A - actual,
    "Forecast_B_excl_jan17": fc_B,
    "Error_B":      fc_B - actual,
})

summary_rows = pd.DataFrame([
    {"Period": "--- SUMMARY ---", "Actual": "", "Forecast_A_original": "",
     "Error_A": "", "Forecast_B_excl_jan17": "", "Error_B": ""},
    {"Period": "MAE (Scenario A)", "Actual": mae_A, "Forecast_A_original": "",
     "Error_A": "", "Forecast_B_excl_jan17": "", "Error_B": ""},
    {"Period": "MAE (Scenario B)", "Actual": mae_B, "Forecast_A_original": "",
     "Error_A": "", "Forecast_B_excl_jan17": "", "Error_B": ""},
    {"Period": "MAPE (Scenario A)", "Actual": f"{mape_A:.2f}%", "Forecast_A_original": "",
     "Error_A": "", "Forecast_B_excl_jan17": "", "Error_B": ""},
    {"Period": "MAPE (Scenario B)", "Actual": f"{mape_B:.2f}%", "Forecast_A_original": "",
     "Error_A": "", "Forecast_B_excl_jan17": "", "Error_B": ""},
    {"Period": "Impact", "Actual": impact, "Forecast_A_original": "",
     "Error_A": "", "Forecast_B_excl_jan17": "", "Error_B": ""},
])
eval_df = pd.concat([eval_df, summary_rows], ignore_index=True)
eval_df.to_csv(REPORTS / "Forecast_Evaluation.csv", index=False)
print(f"\n  [SAVED] reports/Forecast_Evaluation.csv")
print()
print("=" * 60)
print("  Sensitivity check complete.")
print("  Raw data unchanged. Proceed to Excel model next.")
print("=" * 60)
