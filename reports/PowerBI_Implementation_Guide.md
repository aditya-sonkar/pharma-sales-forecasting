# Power BI Implementation Guide — Pharma Sales

This guide provides the exact steps, DAX measures, and visual configurations to build the 3-page Power BI dashboard. It relies entirely on the pre-processed data from Python and Excel. **No new forecasting or complex logic is created in Power BI.**

## 1. Data Import & Modeling

Import the following data sources into Power BI Desktop:

**Source 1: CSV File**
- Path: `data/processed/powerbi_sales.csv`
- Table Name: `powerbi_sales`
- Use: Pages 1 & 2 (Historical Data)

**Source 2: Excel Workbook**
- Path: `excel/Pharma_Forecasting_Model.xlsx`
- Select Sheets: 
  - `4_Forecast_Model` (Rename table to `Forecast_Data`)
  - `5_Accuracy_Test` (Rename table to `Forecast_Accuracy`)
- Use: Page 3 (Forecasting)

**Data Modeling (Relationships):**
Keep it simple. You do not need a complex star schema for this portfolio project.
- You can leave `powerbi_sales` and `Forecast_Data` as separate, independent tables. Page 3 will primarily use `Forecast_Data`. 

---

## 2. DAX Measures

Create a new table called `_Measures` (Enter Data -> blank table) to organize these simple, interview-friendly DAX measures.

### Base Measures (Using `powerbi_sales`)
```dax
Total Sales Quantity = SUM(powerbi_sales[Sales_Quantity])

Average Monthly Sales = 
    AVERAGEX(
        VALUES(powerbi_sales[Year_Month]), 
        CALCULATE(SUM(powerbi_sales[Sales_Quantity]))
    )
```

### YoY Growth (Using `powerbi_sales`)
```dax
Total Sales (Prev Year) = 
    CALCULATE(
        [Total Sales Quantity], 
        SAMEPERIODLASTYEAR(powerbi_sales[Date])
    )

YoY Growth % = 
    DIVIDE(
        [Total Sales Quantity] - [Total Sales (Prev Year)], 
        [Total Sales (Prev Year)], 
        BLANK()
    )
```
*(Note: Because 2019 is a partial year, YoY % for 2019 will reflect Jan-Oct 2019 vs Jan-Oct 2018).*

---

## 3. Page Configurations

### Page 1 — Executive Overview
**Goal:** High-level summary of historical performance.

1. **KPI Cards (Top row):**
   - [Total Sales Quantity]
   - [Average Monthly Sales]
   - [YoY Growth %]
2. **Line Chart (Monthly Sales Trend):**
   - X-Axis: `powerbi_sales[Date]` (Month/Year hierarchy)
   - Y-Axis: `[Total Sales Quantity]`
3. **Bar Chart (Annual Sales):**
   - X-Axis: `powerbi_sales[Year]`
   - Y-Axis: `[Total Sales Quantity]`
   - *Tip: Add a text box noting "2019 is partial (Jan-Oct)"*
4. **Donut Chart (Sales by Category):**
   - Legend: `powerbi_sales[Category]`
   - Values: `[Total Sales Quantity]`
   - Show values as % of grand total.

### Page 2 — Category & Seasonality
**Goal:** Deep dive into ATC categories and seasonal patterns.

1. **Matrix (Month × Year Heatmap):**
   - Rows: `powerbi_sales[Year]`
   - Columns: `powerbi_sales[Month_Name]` (Sort by Month number)
   - Values: `[Total Sales Quantity]`
   - Conditional Formatting: Background color (Lowest = Blue/Green, Highest = Red)
2. **Clustered Bar Chart (Category Ranking):**
   - Y-Axis: `powerbi_sales[Category]`
   - X-Axis: `[Total Sales Quantity]`
3. **Line Chart (Category-wise Monthly Trend):**
   - X-Axis: `powerbi_sales[Date]`
   - Y-Axis: `[Total Sales Quantity]`
   - Legend: `powerbi_sales[Category]`
4. **100% Stacked Column Chart (Year/Category Comparison):**
   - X-Axis: `powerbi_sales[Year]`
   - Y-Axis: `[Total Sales Quantity]`
   - Legend: `powerbi_sales[Category]`

### Page 3 — Forecasting
**Goal:** Display the Excel-generated ETS forecast and validation metrics.

1. **KPI Cards (Validation Metrics):**
   - Use the `Forecast_Accuracy` table to display the MAE and MAPE values for the Jan-Sep 2019 period.
   - You can use Card visuals dragging the `Value` column, filtered by `Metric` = "MAE" or "MAPE".
2. **Line and Clustered Column Chart (Actual vs Forecast):**
   - Use the `Forecast_Data` table.
   - X-Axis: `Forecast_Data[Date]`
   - Column Y-Axis: `Forecast_Data[Actual_Sales]` (Historical)
   - Line Y-Axis: `Forecast_Data[Forecast_ETS]` (Forecast)
   - *Tip: Add `Lower_Bound` and `Upper_Bound` to the Tooltips or as dashed lines to show the 95% confidence interval.*
3. **Table (Future Forecast):**
   - Use `Forecast_Data` table.
   - Filter `Forecast_Data[Status]` to show only "Future Forecast".
   - Columns: `Date`, `Forecast_ETS`, `Lower_Bound`, `Upper_Bound`.

---

## 4. Interview Talking Points

If asked about this dashboard in an interview, say:
> *"I used Power BI strictly for presentation and exploratory visualization. The data transformation was handled in Python (Pandas) and the forecasting was done in Excel using ETS algorithms. I imported the processed CSV and the Excel forecast model directly into Power BI, relying on simple DAX measures to build an intuitive, 3-page executive dashboard. This separated the data engineering, modeling, and presentation layers clearly."*
