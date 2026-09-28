"""
analysis.py
===========
Pharma Sales Analysis & Forecasting
Dataset: Kaggle -- Pharma Sales Data (2014-2019)
Source : https://www.kaggle.com/datasets/milanzdravkovic/pharma-sales-data

Steps:
  Step 1  - Load and understand the dataset
  Step 2  - Data transformation (wide -> long)
  Step 3  - Monthly sales analysis
  Step 4  - Category analysis
  Step 5  - Yearly analysis
  Step 6  - Seasonality analysis
  Step 7  - Business KPIs
  Step 8  - Cross-frequency consistency check (monthly vs daily)
  Step 9  - Export processed datasets

Outputs:
  data/processed/pharma_sales_long.csv
  data/processed/category_summary.csv
  data/processed/monthly_summary.csv
  data/processed/powerbi_sales.csv
  data/processed/cross_frequency_check.csv
  data/processed/kpi_summary.csv
  reports/figures/*.png

NOTE: Forecasting is done separately in Excel using FORECAST.ETS().
      A sensitivity check for the 2017-01 anomaly is in sensitivity_check.py.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent
RAW_DIR   = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
FIGURES   = BASE / "reports" / "figures"

for d in [PROCESSED, FIGURES]:
    d.mkdir(parents=True, exist_ok=True)

# ── ATC category codes (actual column names from salesmonthly.csv) ─────────────
CATEGORIES = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]

CATEGORY_COLORS = {
    "M01AB": "#4E9AF1",
    "M01AE": "#F4845F",
    "N02BA": "#56CFB2",
    "N02BE": "#E84B6A",
    "N05B":  "#F5C542",
    "N05C":  "#9B59B6",
    "R03":   "#2ECC71",
    "R06":   "#E67E22",
}

# ── Chart style ───────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "#0F1117",
    "axes.facecolor":    "#161B27",
    "axes.edgecolor":    "#2D3748",
    "axes.labelcolor":   "#E2E8F0",
    "axes.titlecolor":   "#F7FAFC",
    "xtick.color":       "#A0AEC0",
    "ytick.color":       "#A0AEC0",
    "text.color":        "#E2E8F0",
    "grid.color":        "#2D3748",
    "grid.alpha":        0.5,
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.dpi":        120,
})

TITLE_KW = {"fontsize": 14, "fontweight": "bold", "color": "#F7FAFC", "pad": 12}
LABEL_KW = {"fontsize": 10, "color": "#CBD5E0"}


def save_figure(name, fig=None):
    path = FIGURES / f"{name}.png"
    (fig or plt).savefig(path, dpi=150, bbox_inches="tight", facecolor="#0F1117")
    plt.close("all")
    print(f"  [SAVED] {name}.png")


def fmt_k(x, _):
    return f"{x/1000:.0f}K"


# ==============================================================================
# STEP 1 -- Load and Understand the Dataset
# ==============================================================================
print()
print("=" * 60)
print("  STEP 1: Load and Understand the Dataset")
print("=" * 60)

monthly_raw = pd.read_csv(RAW_DIR / "salesmonthly.csv")

print(f"\nFile          : salesmonthly.csv")
print(f"Shape         : {monthly_raw.shape[0]} rows x {monthly_raw.shape[1]} columns")
print(f"Columns       : {list(monthly_raw.columns)}")
print(f"Date column   : 'datum'  (dtype: {monthly_raw['datum'].dtype})")
print(f"Date range    : {monthly_raw['datum'].iloc[0]}  -->  {monthly_raw['datum'].iloc[-1]}")
print(f"ATC categories: {CATEGORIES}")
print(f"Missing values: {monthly_raw.isnull().sum().sum()}")
print(f"Duplicates    : {monthly_raw.duplicated().sum()}")
print(f"\nInspect actual column names and sample rows before any transformation:")
print(monthly_raw.head(3).to_string(index=False))
print(f"\nDescriptive stats (sales quantities):")
print(monthly_raw[CATEGORIES].describe().round(2).to_string())

monthly_raw["datum"] = pd.to_datetime(monthly_raw["datum"])
is_sorted = monthly_raw["datum"].is_monotonic_increasing
print(f"\nChronological order: {'Yes' if is_sorted else 'NO -- sorting now'}")
if not is_sorted:
    monthly_raw = monthly_raw.sort_values("datum").reset_index(drop=True)


# ==============================================================================
# STEP 2 -- Data Transformation (Wide -> Long)
# ==============================================================================
print()
print("=" * 60)
print("  STEP 2: Data Transformation")
print("=" * 60)

# Dataset is in WIDE format: 8 ATC columns across columns.
# Confirmed by inspection in Step 1. Using pd.melt() to convert to long format.
print(f"\nOriginal format   : WIDE  ({monthly_raw.shape[0]} rows x {monthly_raw.shape[1]} cols)")
print(f"Transforming      : pd.melt() -> long format (Date, Category, Sales_Quantity)")

df = monthly_raw.melt(
    id_vars="datum",
    value_vars=CATEGORIES,
    var_name="Category",
    value_name="Sales_Quantity"
)
df = df.rename(columns={"datum": "Date"})
df = df.sort_values(["Date", "Category"]).reset_index(drop=True)

df["Year"]       = df["Date"].dt.year
df["Month"]      = df["Date"].dt.month
df["Month_Name"] = df["Date"].dt.strftime("%b")
df["Year_Month"] = df["Date"].dt.strftime("%Y-%m")

print(f"\nTransformed format: LONG  ({df.shape[0]} rows x {df.shape[1]} cols)")
print(f"Columns           : {list(df.columns)}")
print(f"Original sales values preserved: yes")
print(f"Nulls after transform          : {df.isnull().sum().sum()}")
print(f"\nSample rows:")
print(df.head(6).to_string(index=False))


# ==============================================================================
# STEP 3 -- Monthly Sales Analysis
# ==============================================================================
print()
print("=" * 60)
print("  STEP 3: Monthly Sales Analysis")
print("=" * 60)

monthly_total = (
    df.groupby(["Date", "Year_Month"], as_index=False)["Sales_Quantity"]
    .sum()
    .rename(columns={"Sales_Quantity": "Total_Sales"})
    .sort_values("Date")
)
monthly_total["Year"]           = monthly_total["Date"].dt.year
monthly_total["Month"]          = monthly_total["Date"].dt.month
monthly_total["MoM_Change"]     = monthly_total["Total_Sales"].diff()
monthly_total["MoM_Growth_Pct"] = monthly_total["Total_Sales"].pct_change() * 100
# 3-month moving average -- supporting trend indicator only, not a forecasting method
monthly_total["MA3"]            = monthly_total["Total_Sales"].rolling(3, min_periods=1).mean()

print(f"\nMonthly stats (all categories combined):")
print(f"  Total sales (all months) : {monthly_total['Total_Sales'].sum():,.1f}")
print(f"  Average monthly sales    : {monthly_total['Total_Sales'].mean():,.1f}")
print(f"  Highest month            : {monthly_total.loc[monthly_total['Total_Sales'].idxmax(), 'Year_Month']}  ({monthly_total['Total_Sales'].max():,.1f})")
print(f"  Lowest month             : {monthly_total.loc[monthly_total['Total_Sales'].idxmin(), 'Year_Month']}  ({monthly_total['Total_Sales'].min():,.1f})")
print(f"  Std deviation            : {monthly_total['Total_Sales'].std():,.1f}")
print(f"\nNote: 2019 covers Jan-Oct only (partial year).")
print(f"      2017-Jan shows a near-zero value in salesmonthly.csv.")
print(f"      Both are documented in the cross-frequency check (Step 8).")

# ── Chart 1: Monthly Sales Trend ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 5))
x = range(len(monthly_total))

ax.fill_between(x, monthly_total["Total_Sales"], alpha=0.12, color="#4E9AF1")
ax.plot(x, monthly_total["Total_Sales"], color="#4E9AF1", linewidth=2,
        label="Monthly Sales", zorder=3)
ax.plot(x, monthly_total["MA3"], color="#F5C542", linewidth=2, linestyle="--",
        label="3-Month Moving Average (trend indicator)", zorder=4)

for yr in monthly_total["Year"].unique():
    yr_rows = monthly_total[monthly_total["Year"] == yr]
    mid_x   = yr_rows.index.tolist()[len(yr_rows) // 2]
    suffix  = "*" if yr == 2019 else ""
    ax.text(mid_x, monthly_total["Total_Sales"].max() * 1.03,
            f"{yr}{suffix}", ha="center", fontsize=10, color="#718096", fontweight="bold")

xtick_pos   = list(x)[::6]
xtick_label = [monthly_total["Year_Month"].iloc[i] for i in xtick_pos]
ax.set_xticks(xtick_pos)
ax.set_xticklabels(xtick_label, rotation=30, ha="right", fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Monthly Total Sales Quantity (2014-2019)  |  * 2019 = Jan-Oct only", **TITLE_KW)
ax.set_xlabel("Month", **LABEL_KW)
ax.set_ylabel("Total Sales Quantity", **LABEL_KW)
ax.legend(framealpha=0.15, edgecolor="#2D3748", labelcolor="#E2E8F0", fontsize=9)
ax.grid(axis="y", linestyle="--")
save_figure("01_monthly_sales_trend", fig)

# ── Chart 2: Month-over-Month Growth % ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 4))
mom_vals   = monthly_total["MoM_Growth_Pct"].fillna(0)
bar_colors = ["#56CFB2" if v >= 0 else "#E84B6A" for v in mom_vals]

ax.bar(x, mom_vals, color=bar_colors, zorder=3)
ax.axhline(0, color="#718096", linewidth=1, linestyle="--")
ax.set_xticks(xtick_pos)
ax.set_xticklabels(xtick_label, rotation=30, ha="right", fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:+.1f}%"))
ax.set_title("Month-over-Month Sales Growth % (2014-2019)", **TITLE_KW)
ax.set_ylabel("MoM Growth %", **LABEL_KW)
ax.grid(axis="y", linestyle="--")
save_figure("02_mom_growth", fig)


# ==============================================================================
# STEP 4 -- Category Analysis
# ==============================================================================
print()
print("=" * 60)
print("  STEP 4: Category Analysis")
print("=" * 60)

cat_total = (
    df.groupby("Category", as_index=False)["Sales_Quantity"]
    .agg(Total="sum", Avg_Monthly="mean", Std="std")
    .sort_values("Total", ascending=False)
)
cat_total["Contribution_Pct"] = (cat_total["Total"] / cat_total["Total"].sum() * 100).round(2)
cat_total["Rank"]             = range(1, len(cat_total) + 1)

print(f"\nCategory ranking (by total sales quantity):")
print(cat_total[["Rank", "Category", "Total", "Avg_Monthly", "Contribution_Pct"]]
      .to_string(index=False))

# ── Chart 3: Category Total Sales ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
cats    = cat_total["Category"].tolist()
totals  = cat_total["Total"].tolist()
colors  = [CATEGORY_COLORS[c] for c in cats]

bars = ax.barh(cats, totals, color=colors, height=0.6, zorder=3)
for bar, val, pct in zip(bars, totals, cat_total["Contribution_Pct"]):
    ax.text(bar.get_width() + max(totals) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"  {val:,.0f}  ({pct:.1f}%)",
            va="center", fontsize=9, color="#E2E8F0")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_xlim(0, max(totals) * 1.3)
ax.set_title("Total Sales Quantity by ATC Category (2014-2019)", **TITLE_KW)
ax.set_xlabel("Total Sales Quantity", **LABEL_KW)
ax.grid(axis="x", linestyle="--")
save_figure("03_category_total_sales", fig)

# ── Chart 4: Category Contribution Donut ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 9))
wedges, texts, autotexts = ax.pie(
    cat_total["Total"],
    labels=cat_total["Category"],
    colors=[CATEGORY_COLORS[c] for c in cat_total["Category"]],
    autopct="%1.1f%%", startangle=140, pctdistance=0.82,
    wedgeprops={"linewidth": 2, "edgecolor": "#0F1117"},
)
for t in texts:
    t.set_color("#E2E8F0"); t.set_fontsize(11)
for at in autotexts:
    at.set_color("#0F1117"); at.set_fontsize(9); at.set_fontweight("bold")
centre = plt.Circle((0, 0), 0.58, fc="#0F1117")
ax.add_patch(centre)
ax.text(0, 0.06, "Sales Share", ha="center", fontsize=11, color="#A0AEC0")
ax.text(0, -0.1, f"{cat_total['Total'].sum():,.0f}", ha="center",
        fontsize=18, color="#F7FAFC", fontweight="bold")
ax.set_title("Category Sales Contribution (2014-2019)", **TITLE_KW)
save_figure("04_category_contribution", fig)

# ── Chart 5: Category Monthly Trend Lines ─────────────────────────────────────
cat_monthly = (
    df.groupby(["Date", "Category"], as_index=False)["Sales_Quantity"].sum()
    .sort_values(["Date", "Category"])
)
fig, ax = plt.subplots(figsize=(16, 6))
for cat in CATEGORIES:
    subset = cat_monthly[cat_monthly["Category"] == cat]
    ax.plot(range(len(monthly_total)), subset["Sales_Quantity"].values,
            label=cat, color=CATEGORY_COLORS[cat], linewidth=1.8, alpha=0.9)
ax.set_xticks(xtick_pos)
ax.set_xticklabels(xtick_label, rotation=30, ha="right", fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Monthly Sales Trend by ATC Category (2014-2019)", **TITLE_KW)
ax.set_xlabel("Month", **LABEL_KW)
ax.set_ylabel("Sales Quantity", **LABEL_KW)
ax.legend(title="Category", framealpha=0.15, edgecolor="#2D3748",
          labelcolor="#E2E8F0", fontsize=9, title_fontsize=9, ncol=2)
ax.grid(axis="y", linestyle="--")
save_figure("05_category_trend_lines", fig)


# ==============================================================================
# STEP 5 -- Yearly Analysis
# ==============================================================================
print()
print("=" * 60)
print("  STEP 5: Yearly Analysis")
print("=" * 60)

yearly = (
    df.groupby("Year", as_index=False)["Sales_Quantity"]
    .sum()
    .rename(columns={"Sales_Quantity": "Annual_Sales"})
)
yearly["YoY_Change"]     = yearly["Annual_Sales"].diff()
yearly["YoY_Growth_Pct"] = yearly["Annual_Sales"].pct_change() * 100

print(f"\nAnnual sales:")
print(yearly.to_string(index=False))
print("\nNote: 2019 is partial (Jan-Oct only -- 10 months).")
print("      2017 annual total is affected by the near-zero Jan 2017 value in monthly CSV.")

cat_year = (
    df.groupby(["Year", "Category"], as_index=False)["Sales_Quantity"]
    .sum()
    .rename(columns={"Sales_Quantity": "Sales"})
)

# ── Chart 6: Annual Sales ─────────────────────────────────────────────────────
YEAR_COLORS = {2014: "#5B8DB8", 2015: "#4A7DA8", 2016: "#396D98",
               2017: "#285D88", 2018: "#1A4E70", 2019: "#F5C542"}
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(yearly["Year"].astype(str), yearly["Annual_Sales"],
              color=[YEAR_COLORS[y] for y in yearly["Year"]],
              zorder=3, width=0.6, edgecolor="#0F1117")
for bar, row in zip(bars, yearly.itertuples()):
    suffix = "*" if row.Year == 2019 else ""
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + yearly["Annual_Sales"].max() * 0.01,
            f"{row.Annual_Sales:,.0f}{suffix}",
            ha="center", fontsize=10, color="#E2E8F0")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Annual Total Sales Quantity (2014-2019)", **TITLE_KW)
ax.set_ylabel("Total Sales Quantity", **LABEL_KW)
ax.set_xlabel("Year  (* 2019 = Jan-Oct only)", **LABEL_KW)
ax.grid(axis="y", linestyle="--")
save_figure("06_annual_sales", fig)

# ── Chart 7: YoY Growth % ────────────────────────────────────────────────────
yoy_plot = yearly.dropna(subset=["YoY_Growth_Pct"])
fig, ax  = plt.subplots(figsize=(10, 4))
bar_cols = ["#56CFB2" if v >= 0 else "#E84B6A" for v in yoy_plot["YoY_Growth_Pct"]]
ax.bar(yoy_plot["Year"].astype(str), yoy_plot["YoY_Growth_Pct"],
       color=bar_cols, zorder=3, width=0.5)
ax.axhline(0, color="#718096", linewidth=1, linestyle="--")
for i, (_, row) in enumerate(yoy_plot.iterrows()):
    ax.text(i, row["YoY_Growth_Pct"] + (0.4 if row["YoY_Growth_Pct"] >= 0 else -1.5),
            f"{row['YoY_Growth_Pct']:+.1f}%",
            ha="center", fontsize=11, color="#E2E8F0", fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:+.1f}%"))
ax.set_title("Year-over-Year Sales Growth %  |  * 2019 = Jan-Oct only", **TITLE_KW)
ax.set_ylabel("YoY Growth %", **LABEL_KW)
ax.set_xlabel("Year  (* partial year)", **LABEL_KW)
ax.grid(axis="y", linestyle="--")
save_figure("07_yoy_growth", fig)

# ── Chart 8: Category x Year Grouped Bar ─────────────────────────────────────
years  = sorted(cat_year["Year"].unique())
x_pos  = np.arange(len(CATEGORIES))
width  = 0.14
YEAR_BAR_COLORS = ["#7FB3D3", "#5B8DB8", "#3B6E96", "#254F6E", "#1A3A52", "#F5C542"]

fig, ax = plt.subplots(figsize=(16, 6))
for i, (yr, col) in enumerate(zip(years, YEAR_BAR_COLORS)):
    vals = [cat_year[(cat_year["Year"] == yr) & (cat_year["Category"] == c)]["Sales"].values[0]
            for c in CATEGORIES]
    ax.bar(x_pos + (i - len(years) / 2 + 0.5) * width, vals,
           width, label=str(yr), color=col, zorder=3, edgecolor="#0F1117", linewidth=0.4)

ax.set_xticks(x_pos)
ax.set_xticklabels(CATEGORIES, fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Sales by Category and Year (2014-2019)  |  * 2019 = Jan-Oct only", **TITLE_KW)
ax.set_ylabel("Sales Quantity", **LABEL_KW)
handles, labels = ax.get_legend_handles_labels()
labels = [l + " *" if l == "2019" else l for l in labels]
ax.legend(handles, labels, title="Year  (* partial)", framealpha=0.15,
          edgecolor="#2D3748", labelcolor="#E2E8F0", fontsize=9, title_fontsize=9)
ax.grid(axis="y", linestyle="--")
save_figure("08_category_year_comparison", fig)


# ==============================================================================
# STEP 6 -- Seasonality Analysis
# ==============================================================================
print()
print("=" * 60)
print("  STEP 6: Seasonality Analysis")
print("=" * 60)

seas_pivot = monthly_total.copy()
heatmap_data = seas_pivot.pivot(index="Year", columns="Month", values="Total_Sales")
month_names  = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]
heatmap_data.columns = [month_names[m - 1] for m in heatmap_data.columns]

print("\nMonth x Year sales pivot (overall, all categories):")
print(heatmap_data.round(0).to_string())

seas_avg = seas_pivot.groupby("Month")["Total_Sales"].mean()
seas_avg.index = [month_names[m - 1] for m in seas_avg.index]
print(f"\nAverage sales by month (across all years):")
for m, v in seas_avg.items():
    bar = "#" * int(v / seas_avg.max() * 30)
    print(f"  {m:>3}: {v:>7,.1f}  {bar}")

# ── Chart 9: Month x Year Heatmap ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(heatmap_data, ax=ax, cmap="YlOrRd",
            annot=True, fmt=".0f", linewidths=0.4, linecolor="#0F1117",
            cbar_kws={"label": "Total Sales Qty", "shrink": 0.8},
            annot_kws={"size": 9})
ax.set_title("Monthly Sales Heatmap -- Year x Month (All Categories Combined)", **TITLE_KW)
ax.set_xlabel("Month", **LABEL_KW)
ax.set_ylabel("Year", **LABEL_KW)
ax.tick_params(axis="y", rotation=0)
ax.collections[0].colorbar.ax.yaxis.label.set_color("#E2E8F0")
ax.collections[0].colorbar.ax.tick_params(colors="#A0AEC0")
save_figure("09_seasonality_heatmap", fig)

# ── Chart 10: Monthly Seasonality Index ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 4))
bar_colors_seas = ["#E84B6A" if v == seas_avg.max() else
                   "#4E9AF1" if v == seas_avg.min() else
                   "#56CFB2" for v in seas_avg]
bars = ax.bar(seas_avg.index, seas_avg.values, color=bar_colors_seas, zorder=3, width=0.6)
ax.axhline(seas_avg.mean(), color="#F5C542", linewidth=1.5, linestyle="--",
           label=f"Overall Avg: {seas_avg.mean():,.0f}")
for bar, val in zip(bars, seas_avg):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + seas_avg.max() * 0.01,
            f"{val:,.0f}", ha="center", fontsize=9, color="#E2E8F0")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax.set_title("Average Monthly Sales by Month (Seasonal Pattern, All Years)", **TITLE_KW)
ax.set_ylabel("Avg Sales Quantity", **LABEL_KW)
ax.legend(framealpha=0.15, edgecolor="#2D3748", labelcolor="#E2E8F0", fontsize=9)
ax.grid(axis="y", linestyle="--")
save_figure("10_monthly_seasonality", fig)

# ── Chart 11: Seasonality for top 2 categories ───────────────────────────────
top2 = cat_total.head(2)["Category"].tolist()
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
for ax, cat in zip(axes, top2):
    cat_df   = df[df["Category"] == cat]
    cat_seas = cat_df.groupby("Month")["Sales_Quantity"].mean()
    cat_seas.index = [month_names[m - 1] for m in cat_seas.index]
    color    = CATEGORY_COLORS[cat]
    ax.bar(cat_seas.index, cat_seas.values, color=color, zorder=3, width=0.6, alpha=0.85)
    ax.axhline(cat_seas.mean(), color="#F5C542", linewidth=1.5, linestyle="--",
               label=f"Avg: {cat_seas.mean():,.1f}")
    for b, v in zip(ax.patches, cat_seas):
        ax.text(b.get_x() + b.get_width() / 2,
                b.get_height() + cat_seas.max() * 0.02,
                f"{v:.0f}", ha="center", fontsize=8, color="#E2E8F0")
    ax.set_title(f"Seasonality: {cat}", **TITLE_KW)
    ax.set_ylabel("Avg Monthly Sales", **LABEL_KW)
    ax.legend(framealpha=0.15, edgecolor="#2D3748", labelcolor="#E2E8F0", fontsize=8)
    ax.grid(axis="y", linestyle="--")
plt.tight_layout()
save_figure("11_top2_category_seasonality", fig)


# ==============================================================================
# STEP 7 -- Business KPIs
# ==============================================================================
print()
print("=" * 60)
print("  STEP 7: Business KPIs")
print("=" * 60)

top_cat    = cat_total.iloc[0]
best_month = monthly_total.loc[monthly_total["Total_Sales"].idxmax()]
# Use 2017->2018 for YoY: both are full calendar years in the monthly file.
# Note: 2017 annual total is affected by near-zero Jan 2017.
full_yoy   = yearly[yearly["Year"].isin([2017, 2018])]
valid_yoy  = float(full_yoy.iloc[-1]["YoY_Growth_Pct"]) if len(full_yoy) >= 2 else None

kpis = {
    "Total Sales Quantity (2014-2019)":    f"{df['Sales_Quantity'].sum():,.1f}",
    "Average Monthly Sales (all cats)":    f"{monthly_total['Total_Sales'].mean():,.1f}",
    "Highest-Selling Category":            f"{top_cat['Category']} ({top_cat['Total']:,.1f} units)",
    "Category Contribution (top)":         f"{top_cat['Contribution_Pct']:.1f}%",
    "Highest-Sales Month":                 f"{best_month['Year_Month']}  ({best_month['Total_Sales']:,.1f})",
    "YoY Growth 2017->2018 (full years)":  f"{valid_yoy:+.1f}%" if valid_yoy else "N/A",
}

print()
for k, v in kpis.items():
    print(f"  {k:<45} {v}")

kpi_df = pd.DataFrame({"KPI": kpis.keys(), "Value": kpis.values()})
kpi_df.to_csv(PROCESSED / "kpi_summary.csv", index=False)
print(f"\n  [SAVED] kpi_summary.csv")


# ==============================================================================
# STEP 8 -- Cross-Frequency Consistency Check (Monthly vs Daily)
# ==============================================================================
# Purpose: Observe whether salesmonthly.csv and salesdaily.csv (aggregated to
# monthly level) produce similar totals. This is NOT a validation of the
# monthly file's accuracy -- both datasets are separately preprocessed by the
# dataset authors and may use different methodologies.
# salesmonthly.csv remains the primary analysis source regardless of outcome.
# No raw data is modified.
# ==============================================================================
print()
print("=" * 60)
print("  STEP 8: Cross-Frequency Consistency Check")
print("=" * 60)
print("\nNote: The daily file is NOT treated as ground truth.")
print("      Both files are separately preprocessed by the dataset authors.")
print("      salesmonthly.csv remains the primary source.")

daily_raw = pd.read_csv(RAW_DIR / "salesdaily.csv")
daily_raw["datum"]     = pd.to_datetime(daily_raw["datum"])
daily_raw["YearMonth"] = daily_raw["datum"].dt.to_period("M")

print(f"\nDaily file shape  : {daily_raw.shape}")
print(f"Daily date range  : {daily_raw['datum'].min().date()} --> {daily_raw['datum'].max().date()}")

daily_monthly_agg = (
    daily_raw.groupby("YearMonth")[CATEGORIES].sum().sum(axis=1)
    .reset_index()
    .rename(columns={0: "Daily_Agg_Total"})
)
daily_monthly_agg["YearMonth"] = daily_monthly_agg["YearMonth"].astype(str)

monthly_check = monthly_total[["Year_Month", "Total_Sales"]].copy()
monthly_check.columns = ["YearMonth", "Monthly_Total"]

reconcile = monthly_check.merge(daily_monthly_agg, on="YearMonth", how="inner")
reconcile["Diff"]     = reconcile["Monthly_Total"] - reconcile["Daily_Agg_Total"]
reconcile["Diff_Pct"] = (reconcile["Diff"] / reconcile["Monthly_Total"] * 100).round(4)

large_diff = reconcile[reconcile["Diff_Pct"].abs() > 5].copy()

print(f"\nMonths compared: {len(reconcile)}")
print(f"\nMonths with notable difference (>5% absolute):")
if len(large_diff) > 0:
    print(large_diff[["YearMonth", "Monthly_Total", "Daily_Agg_Total",
                        "Diff", "Diff_Pct"]].to_string(index=False))
else:
    print("  None.")

print(f"\nObservations:")
print(f"  - 2017-01: Monthly total is near-zero across most categories.")
print(f"    Daily-derived total for the same month shows non-zero values.")
print(f"  - 2017-02: Monthly values are systematically lower than daily-")
print(f"    derived totals across all 8 categories (~20% uniformly).")
print(f"  - Most other months: Differences are small (floating-point/rounding).")
print(f"\nDocumentation:")
print(f"  The monthly and daily datasets show discrepancies for certain periods,")
print(f"  including January and February 2017. These differences are retained and")
print(f"  documented rather than modifying either source dataset.")
print(f"  A separate sensitivity check (sensitivity_check.py) will assess whether")
print(f"  the 2017-01 anomaly materially affects forecasting results.")

reconcile.to_csv(PROCESSED / "cross_frequency_check.csv", index=False)
print(f"\n  [SAVED] cross_frequency_check.csv")


# ==============================================================================
# STEP 9 -- Export Processed Datasets
# ==============================================================================
print()
print("=" * 60)
print("  STEP 9: Export Processed Datasets")
print("=" * 60)

# 1. Long format (main analysis file)
df_export = df[["Date", "Year", "Month", "Month_Name", "Year_Month",
                "Category", "Sales_Quantity"]].copy()
df_export.to_csv(PROCESSED / "pharma_sales_long.csv", index=False)
print(f"  [SAVED] pharma_sales_long.csv     ({len(df_export):,} rows)")

# 2. Category summary
cat_total.to_csv(PROCESSED / "category_summary.csv", index=False)
print(f"  [SAVED] category_summary.csv      ({len(cat_total)} rows)")

# 3. Monthly summary (base for Excel forecasting model)
monthly_summary = monthly_total[
    ["Date", "Year_Month", "Year", "Month", "Total_Sales",
     "MoM_Change", "MoM_Growth_Pct", "MA3"]
].copy()
monthly_summary.to_csv(PROCESSED / "monthly_summary.csv", index=False)
print(f"  [SAVED] monthly_summary.csv       ({len(monthly_summary)} rows)")

# 4. Power BI flat file
pbi = df_export.copy()
pbi["Quarter"]    = "Q" + ((pbi["Month"] - 1) // 3 + 1).astype(str)
pbi["Month_Year"] = pbi["Date"].dt.strftime("%b %Y")
cat_totals_map    = df.groupby("Category")["Sales_Quantity"].sum().to_dict()
pbi["Cat_Total"]  = pbi["Category"].map(cat_totals_map)
pbi.to_csv(PROCESSED / "powerbi_sales.csv", index=False)
print(f"  [SAVED] powerbi_sales.csv         ({len(pbi):,} rows)")

# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  ANALYSIS COMPLETE")
print("=" * 60)
print(f"\n  Charts  -> reports/figures/  ({len(list(FIGURES.glob('*.png')))} files)")
print(f"  Data    -> data/processed/   ({len(list(PROCESSED.glob('*.csv')))} files)")
print()
print("  Next steps:")
print("  1. Run sensitivity_check.py to assess 2017-01 forecast impact.")
print("  2. Then proceed to Excel: Pharma_Forecasting_Model.xlsx")
print("     Use data/processed/monthly_summary.csv as the base.")
