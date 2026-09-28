import pandas as pd

CATEGORIES = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']

monthly = pd.read_csv('data/raw/salesmonthly.csv')
monthly['datum'] = pd.to_datetime(monthly['datum'])

daily = pd.read_csv('data/raw/salesdaily.csv')
daily['datum'] = pd.to_datetime(daily['datum'], dayfirst=False)

SEP = "=" * 70

# ── 2017-01 ───────────────────────────────────────────────────────────────────
print(SEP)
print("INVESTIGATION: 2017-01")
print(SEP)

m_jan17 = monthly[monthly['datum'].dt.to_period('M') == '2017-01']
d_jan17 = daily[daily['datum'].dt.to_period('M') == pd.Period('2017-01')]

print("\n[A] Raw salesmonthly.csv row for 2017-01:")
print(m_jan17.to_string(index=False))

print(f"\n[B] salesdaily.csv rows for January 2017:  ({len(d_jan17)} rows)")
print(d_jan17[['datum'] + CATEGORIES].to_string(index=False))

print("\n[C] Category-level comparison — Monthly vs Daily-Aggregated (2017-01):")
hdr = f"  {'Category':<8}  {'Monthly':>12}  {'Daily_Agg':>12}  {'Diff':>12}"
print(hdr)
print("  " + "-" * 50)
for cat in CATEGORIES:
    m_val = float(m_jan17[cat].values[0]) if len(m_jan17) > 0 else float('nan')
    d_val = float(d_jan17[cat].sum())
    diff  = m_val - d_val
    print(f"  {cat:<8}  {m_val:>12.4f}  {d_val:>12.4f}  {diff:>12.4f}")

print("\n[D] Exact raw dtype and value per category in monthly CSV (2017-01):")
for cat in CATEGORIES:
    val = m_jan17[cat].values[0]
    print(f"  {cat}: value={repr(val)}  dtype={type(val).__name__}")

print(f"\n[E] datum value in monthly CSV : {repr(m_jan17['datum'].values[0])}")
print(f"    Daily Jan 2017 date range  : "
      f"{d_jan17['datum'].min().date()} -> {d_jan17['datum'].max().date()}")
print(f"    Daily Jan 2017 row count   : {len(d_jan17)}")

# ── 2017-02 ───────────────────────────────────────────────────────────────────
print()
print(SEP)
print("INVESTIGATION: 2017-02")
print(SEP)

m_feb17 = monthly[monthly['datum'].dt.to_period('M') == '2017-02']
d_feb17 = daily[daily['datum'].dt.to_period('M') == pd.Period('2017-02')]

print("\n[A] Raw salesmonthly.csv row for 2017-02:")
print(m_feb17.to_string(index=False))

print(f"\n[B] salesdaily.csv rows for February 2017:  ({len(d_feb17)} rows)")
print(d_feb17[['datum'] + CATEGORIES].to_string(index=False))

print("\n[C] Category-level comparison — Monthly vs Daily-Aggregated (2017-02):")
print(hdr)
print("  " + "-" * 50)
for cat in CATEGORIES:
    m_val = float(m_feb17[cat].values[0]) if len(m_feb17) > 0 else float('nan')
    d_val = float(d_feb17[cat].sum())
    diff  = m_val - d_val
    flag  = "  <-- discrepancy" if abs(diff) > 1 else ""
    print(f"  {cat:<8}  {m_val:>12.4f}  {d_val:>12.4f}  {diff:>12.4f}{flag}")

# ── Coverage ──────────────────────────────────────────────────────────────────
print()
print(SEP)
print("COVERAGE CHECK")
print(SEP)
print(f"\nMonthly date range  : {monthly['datum'].min().date()} -> {monthly['datum'].max().date()}")
print(f"Daily date range    : {daily['datum'].min().date()} -> {daily['datum'].max().date()}")
print(f"\nTotal months in monthly CSV  : {len(monthly)}")
print(f"Total months in daily CSV    : {daily['datum'].dt.to_period('M').nunique()}")

# Check rows immediately before and after 2017-01 in monthly
idx = monthly[monthly['datum'].dt.to_period('M') == '2017-01'].index[0]
print(f"\n[F] Monthly rows around 2017-01 (context):")
print(monthly.iloc[max(0, idx-1):idx+2].to_string(index=False))
