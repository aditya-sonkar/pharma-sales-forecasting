import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent
PROCESSED = BASE / "data" / "processed"
EXCEL_DIR = BASE / "excel"
EXCEL_DIR.mkdir(parents=True, exist_ok=True)
FILE_PATH = EXCEL_DIR / "Pharma_Forecasting_Model.xlsx"

# ── Load Data ─────────────────────────────────────────────────────────────────
monthly  = pd.read_csv(PROCESSED / "monthly_summary.csv")
category = pd.read_csv(PROCESSED / "category_summary.csv")
kpis     = pd.read_csv(PROCESSED / "kpi_summary.csv")

# Ensure Data is sorted
monthly["Date"] = pd.to_datetime(monthly["Date"])
monthly = monthly.sort_values("Date").reset_index(drop=True)

# ── Styles ────────────────────────────────────────────────────────────────────
wb = Workbook()

header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="2D3748", end_color="2D3748", fill_type="solid")
align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")

def apply_header(ws, row=1):
    for cell in ws[row]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

def auto_adjust_cols(ws):
    for col in ws.columns:
        max_length = 0
        col_letter = None
        for cell in col:
            # Skip MergedCells
            if type(cell).__name__ == 'MergedCell':
                continue
            if not col_letter:
                col_letter = cell.column_letter
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        if col_letter:
            adjusted_width = (max_length + 3)
            ws.column_dimensions[col_letter].width = min(adjusted_width, 40)

# ── 1. Cover / Executive Summary ─────────────────────────────────────────────
ws1 = wb.active
ws1.title = "1_Executive_Summary"

ws1["A1"] = "Pharma Sales Analysis & Forecasting Model"
ws1["A1"].font = Font(size=16, bold=True)
ws1.merge_cells("A1:D1")

ws1["A3"] = "Dataset Overview:"
ws1["A3"].font = Font(bold=True)
ws1["A4"] = "Source: Kaggle Pharma Sales Data (2014-2019)"
ws1["A5"] = "Primary File: salesmonthly.csv"
ws1["A6"] = "Training Period: Jan 2014 - Dec 2018 (60 months)"
ws1["A7"] = "Validation Period: Jan 2019 - Sep 2019 (9 months)"
ws1["A8"] = "Note: Oct 2019 excluded from validation as it is a partial month."

ws1["A10"] = "Key Findings & Limitations:"
ws1["A10"].font = Font(bold=True)
ws1["A11"] = "1. Jan 2017 shows anomalous near-zero sales in the raw data."
ws1["A12"] = "2. A sensitivity check showed a modest change in forecast error when the January 2017 anomaly was excluded."
ws1["A13"] = "3. The original data is retained; no synthetic imputation was performed."

ws1["A15"] = "Business KPIs:"
ws1["A15"].font = Font(bold=True)
row_idx = 16
for _, row in kpis.iterrows():
    ws1[f"A{row_idx}"] = row["KPI"]
    ws1[f"B{row_idx}"] = row["Value"]
    row_idx += 1

auto_adjust_cols(ws1)

# ── 2. Data Input ─────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("2_Data_Input")
cols2 = ["Date", "Year_Month", "Year", "Month", "Total_Sales", "MoM_Change", "MoM_Growth_Pct", "MA3"]
ws2.append(cols2)
for _, row in monthly.iterrows():
    ws2.append([row[c] for c in cols2])
apply_header(ws2)
auto_adjust_cols(ws2)

# ── 3. Category Input ─────────────────────────────────────────────────────────
ws3 = wb.create_sheet("3_Category_Input")
cols3 = ["Rank", "Category", "Total", "Avg_Monthly", "Contribution_Pct"]
ws3.append(cols3)
for _, row in category.iterrows():
    ws3.append([row[c] for c in cols3])
apply_header(ws3)
auto_adjust_cols(ws3)

# ── 4. Forecast Model ─────────────────────────────────────────────────────────
ws4 = wb.create_sheet("4_Forecast_Model")
ws4.append(["Date", "Actual_Sales", "Forecast_ETS", "Lower_Bound", "Upper_Bound", "Status"])
apply_header(ws4)

# Create a master timeline: Jan 2014 to Dec 2020
start_date = pd.to_datetime("2014-01-31")
timeline = pd.date_range(start="2014-01-31", periods=84, freq="M")

for i, dt in enumerate(timeline):
    row_idx = i + 2
    ws4[f"A{row_idx}"] = dt.date()
    
    # Actual Sales (if available, up to index 69 which is Oct 2019)
    if i < len(monthly):
        ws4[f"B{row_idx}"] = monthly.loc[i, "Total_Sales"]
        status = "Training" if dt.year <= 2018 else "Validation (Partial)"
        if dt.year == 2019 and dt.month <= 9:
            status = "Validation (Full Month)"
    else:
        ws4[f"B{row_idx}"] = ""
        status = "Future Forecast"
        
    ws4[f"F{row_idx}"] = status

# Validation Period (Jan 2019 - Sep 2019, rows 62 to 70)
# Training data is B2:B61 (Jan 2014 - Dec 2018)
for row_idx in range(62, 71):
    ws4[f"C{row_idx}"] = f"=FORECAST.ETS(A{row_idx}, B$2:B$61, A$2:A$61, 1, 1)"
    ws4[f"D{row_idx}"] = f"=C{row_idx} - FORECAST.ETS.CONFINT(A{row_idx}, B$2:B$61, A$2:A$61, 0.95, 1, 1)"
    ws4[f"E{row_idx}"] = f"=C{row_idx} + FORECAST.ETS.CONFINT(A{row_idx}, B$2:B$61, A$2:A$61, 0.95, 1, 1)"

# Future Forecast Period (Oct 2019 onwards, rows 71 to 85)
# Training data is B2:B70 (Jan 2014 - Sep 2019). We exclude Oct 2019 (row 71) actuals from training because it's partial.
for row_idx in range(71, 86):
    ws4[f"C{row_idx}"] = f"=FORECAST.ETS(A{row_idx}, B$2:B$70, A$2:A$70, 1, 1)"
    ws4[f"D{row_idx}"] = f"=C{row_idx} - FORECAST.ETS.CONFINT(A{row_idx}, B$2:B$70, A$2:A$70, 0.95, 1, 1)"
    ws4[f"E{row_idx}"] = f"=C{row_idx} + FORECAST.ETS.CONFINT(A{row_idx}, B$2:B$70, A$2:A$70, 0.95, 1, 1)"

auto_adjust_cols(ws4)

# ── 5. Accuracy Test (Validation) ─────────────────────────────────────────────
ws5 = wb.create_sheet("5_Accuracy_Test")
ws5.append(["Metric", "Validation Period", "Value", "Formula/Logic"])
apply_header(ws5)

ws5.append(["Validation Scope", "Jan 2019 - Sep 2019 (9 months)", "", "Filtered out Oct 2019 (partial)"])
ws5.append(["MAE (Mean Absolute Error)", "", "=AVERAGE(ABS(C3-B3), ABS(C4-B4), ABS(C5-B5), ABS(C6-B6), ABS(C7-B7), ABS(C8-B8), ABS(C9-B9), ABS(C10-B10), ABS(C11-B11))", "Calculated on Jan-Sep 2019"])
ws5.append(["MAPE (Mean Absolute Pct Error)", "", "=AVERAGE(ABS((C3-B3)/B3), ABS((C4-B4)/B4), ABS((C5-B5)/B5), ABS((C6-B6)/B6), ABS((C7-B7)/B7), ABS((C8-B8)/B8), ABS((C9-B9)/B9), ABS((C10-B10)/B10), ABS((C11-B11)/B11))", "Calculated on Jan-Sep 2019"])

ws5.append([])
ws5.append(["Date", "Actual_Sales", "Forecast_Sales", "Absolute_Error", "Absolute_Pct_Error"])
header_row_idx = 6
apply_header(ws5, row=header_row_idx)

# Copy Jan-Sep 2019 data (rows 62 to 70 from Forecast sheet)
for i, forecast_row in enumerate(range(62, 71)):
    val_row = header_row_idx + 1 + i
    ws5[f"A{val_row}"] = f"='4_Forecast_Model'!A{forecast_row}"
    ws5[f"B{val_row}"] = f"='4_Forecast_Model'!B{forecast_row}"
    ws5[f"C{val_row}"] = f"='4_Forecast_Model'!C{forecast_row}"
    ws5[f"D{val_row}"] = f"=ABS(C{val_row}-B{val_row})"
    ws5[f"E{val_row}"] = f"=D{val_row}/B{val_row}"

auto_adjust_cols(ws5)

# ── Save ──────────────────────────────────────────────────────────────────────
wb.save(FILE_PATH)
print(f"Excel Model generated at: {FILE_PATH}")
