# 💊 Pharma Sales Analysis & Demand Forecasting

A comprehensive data analytics and forecasting project demonstrating end-to-end business intelligence workflows. This project leverages **Python** for data processing, **Excel** for statistical forecasting, and **Power BI** for executive reporting.

---

## 🎯 Project Objectives
- **Data Transformation & EDA:** Convert raw, wide-format pharmaceutical data into actionable insights using Python.
- **Data Quality & Validation:** Perform cross-frequency consistency checks to identify and assess historical data anomalies.
- **Time-Series Forecasting:** Build an `ETS` (Error, Trend, Seasonality) forecast model to predict future demand.
- **Executive Reporting:** Deliver a clean, business-focused dashboard using Power BI.

---

## 📂 Repository Structure

```text
Pharma Sales Analysis/
├── data/          # Raw and processed datasets
├── excel/         # Final Excel forecasting model & accuracy testing
├── python/        # Python scripts for EDA, validation, and transformations
└── reports/       # Exported charts, evaluation reports, and Power BI guide
```

---

## 🧠 Methodology & Key Insights

### 1. Transparent Data Validation
Instead of blindly trusting the dataset, we performed a cross-frequency check between the monthly and daily datasets. 
- **The Catch:** We discovered near-zero sales anomalies in January 2017.
- **The Solution:** Rather than manipulating or inventing synthetic data, we retained the raw data and ran a programmatic sensitivity check. The analysis proved the anomaly had a minimal impact (2-3% MAE difference) on the long-term forecast, ensuring data integrity was maintained.

### 2. Robust Forecasting Strategy
To accurately validate the Excel `FORECAST.ETS` model:
- **Training Period:** Jan 2014 – Dec 2018 (60 months)
- **Validation Period:** Jan 2019 – Sep 2019 (9 months)
- *Note:* October 2019 was explicitly excluded from validation testing as it was identified as a partial month, preventing skewed accuracy metrics (MAPE).

---

## 🚀 Getting Started

To reproduce the analysis locally:

1. **Run the Data Pipeline (Python):**
   ```bash
   pip install -r python/requirements.txt
   python python/analysis.py
   python python/sensitivity_check.py
   python python/create_excel_model.py
   ```
2. **Review the Forecast (Excel):**
   Open `excel/Pharma_Forecasting_Model.xlsx` to explore the ETS forecast, confidence bounds, and validation metrics.
3. **Build the Dashboard (Power BI):**
   Check out `reports/PowerBI_Implementation_Guide.md` for a step-by-step guide on recreating the interactive executive dashboard.

---
*Built as a portfolio project showcasing programmatic data wrangling, transparent data-quality handling, and business-focused demand planning.*
