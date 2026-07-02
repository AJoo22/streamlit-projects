# Streamlit Portfolio Apps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert 6 of the 7 `data-analysis-portfolio` projects into interactive Streamlit dashboards living in `streamlit-projects/projects/`.

**Architecture:** Each app is a self-contained folder with a thin `app.py` (Streamlit UI: sidebar filters, KPI tiles, Plotly charts, data table, download button) that imports pure, unit-tested functions from a sibling `data.py` (loading, filtering, aggregation, KPI computation). Bundled anonymized CSVs live in each app's `data/` folder.

**Tech Stack:** Python 3.11+, Streamlit >=1.30, Plotly >=5, pandas >=2, pytest, scikit-learn + statsmodels (energy app only).

## Global Constraints

- Every app folder follows the exact structure: `app.py`, `data.py`, `requirements.txt`, `README.md`, `data/<csv files>`, `tests/test_data.py`, `.github/workflows/streamlit.yml`.
- Every `data.py` function is pure (no Streamlit calls, no I/O side effects beyond `load_data` reading its CSV) so it is testable with plain pytest.
- Every `app.py` wraps its `load_data` call in `@st.cache_data`.
- Every filtered-dataframe code path must handle the empty case: `if filtered.empty: st.warning("No data matches the selected filters."); st.stop()` before computing KPIs/charts on it.
- Every `st.plotly_chart(...)` call passes `use_container_width=True`.
- Data cleaning/coercion happens inside `data.py` functions, never in `app.py`, so cached functions don't trigger Streamlit mutation warnings.
- No automated UI test suite — `tests/test_data.py` covers `data.py` only. Each app task's manual verification step is running `streamlit run app.py --server.headless true` and confirming no traceback, then killing the process.
- Source CSVs are read from `data-analysis-portfolio` (path: `/Users/amine_jalili/Desktop/test/data-analysis-portfolio/<project>/<file>.csv`) and copied into each app's own `data/` folder — never referenced cross-repo at runtime.

---

## Task 1: Energy dataset sample + shared CI workflow template

**Files:**
- Create: `/Users/amine_jalili/Desktop/test/streamlit-projects/scripts/generate_energy_sample.py`
- Create: `/Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard/data/eco2mix_sample.csv` (generated output)

**Interfaces:**
- Produces: `eco2mix_sample.csv` with columns `Région;Date;Consommation (MW);Thermique (MW);Nucléaire (MW);Eolien (MW);Solaire (MW);Hydraulique (MW);Pompage (MW);Bioénergies (MW);TCO Thermique (%);TCO Nucléaire (%);TCO Eolien (%);TCO Hydraulique (%);TCO Solaire (%);TCO Bioénergies (%)` — consumed by Task 2.

- [ ] **Step 1: Write the sample-generation script**

```python
# /Users/amine_jalili/Desktop/test/streamlit-projects/scripts/generate_energy_sample.py
import pandas as pd

SRC = "/Users/amine_jalili/Archive/data_analysis_Portfolio-source-2026-07-03/jeuxDeDonéesDataScientest/eco2mix-regional-cons-def copie.csv"
DST = "/Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard/data/eco2mix_sample.csv"

COLUMNS = [
    "Région", "Date", "Consommation (MW)", "Thermique (MW)", "Nucléaire (MW)",
    "Eolien (MW)", "Solaire (MW)", "Hydraulique (MW)", "Pompage (MW)",
    "Bioénergies (MW)", "TCO Thermique (%)", "TCO Nucléaire (%)",
    "TCO Eolien (%)", "TCO Hydraulique (%)", "TCO Solaire (%)", "TCO Bioénergies (%)",
]
REGIONS = ["Île-de-France", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine"]
MIN_DATE = "2021-01-01"

def main():
    chunks = []
    reader = pd.read_csv(SRC, sep=";", usecols=COLUMNS, parse_dates=["Date"], chunksize=200_000, low_memory=False)
    for chunk in reader:
        chunk = chunk[chunk["Région"].isin(REGIONS) & (chunk["Date"] >= MIN_DATE)]
        if not chunk.empty:
            chunks.append(chunk)
    sample = pd.concat(chunks, ignore_index=True)
    sample.to_csv(DST, sep=";", index=False)
    print(f"Wrote {len(sample)} rows to {DST}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create the destination directory and run the script**

```bash
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard/data
python3 /Users/amine_jalili/Desktop/test/streamlit-projects/scripts/generate_energy_sample.py
```

Expected: prints `Wrote <N> rows to .../eco2mix_sample.csv` with N > 0.

- [ ] **Step 3: Verify the sample is reasonably sized for git**

```bash
du -h /Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard/data/eco2mix_sample.csv
wc -l /Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard/data/eco2mix_sample.csv
```

Expected: file size well under 25MB (GitHub's soft warning threshold). If it's larger, reduce to 2 regions or 1 year in `MIN_DATE`/`REGIONS` and rerun Step 2.

- [ ] **Step 4: Write the shared CI workflow template (used by every app, parameterized per folder in each app's own task)**

This is documentation, not a file — record the template here for reuse in Tasks 3, 5, 7, 9, 11, 13:

```yaml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/<APP_FOLDER>/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/<APP_FOLDER>
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Commit**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects
git add scripts/generate_energy_sample.py projects/energy-consumption-dashboard/data/eco2mix_sample.csv
git commit -m "Add energy dataset sample generator and trimmed sample CSV"
```

---

## Task 2: energy-consumption-dashboard — data module + tests

**Files:**
- Create: `projects/energy-consumption-dashboard/data.py`
- Test: `projects/energy-consumption-dashboard/tests/test_data.py`

**Interfaces:**
- Consumes: `data/eco2mix_sample.csv` (from Task 1)
- Produces (used by Task 3's `app.py`): `load_data(path) -> pd.DataFrame`, `filter_data(df, regions, start_date, end_date) -> pd.DataFrame`, `compute_kpis(df) -> dict`, `consumption_by_region(df) -> pd.Series`, `production_mix(df) -> pd.Series`, `production_over_time(df) -> pd.DataFrame`, `fit_regression(df) -> dict | None`, `fit_forecast(df, region, periods=12) -> dict | None`

- [ ] **Step 1: Write the failing tests**

```python
# projects/energy-consumption-dashboard/tests/test_data.py
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_df():
    rows = []
    dates = pd.date_range("2021-01-01", periods=40, freq="D")
    for i, date in enumerate(dates):
        rows.append({
            "Région": "Île-de-France" if i % 2 == 0 else "Nouvelle-Aquitaine",
            "Date": date,
            "Consommation (MW)": 1000 + i * 10,
            "Thermique (MW)": 100 + i,
            "Nucléaire (MW)": 500 + i,
            "Eolien (MW)": 50,
            "Solaire (MW)": 20,
            "Hydraulique (MW)": 80,
            "Pompage (MW)": 5,
            "Bioénergies (MW)": 10,
            "TCO Thermique (%)": 10.0,
            "TCO Nucléaire (%)": 50.0,
            "TCO Eolien (%)": 5.0,
            "TCO Hydraulique (%)": 8.0,
            "TCO Solaire (%)": 2.0,
            "TCO Bioénergies (%)": 1.0,
        })
    return pd.DataFrame(rows)


def test_load_data(tmp_path):
    df = make_df()
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, sep=";", index=False)
    loaded = d.load_data(str(csv_path))
    assert "Production (MW)" in loaded.columns
    assert pd.api.types.is_datetime64_any_dtype(loaded["Date"])


def test_filter_data():
    df = make_df()
    filtered = d.filter_data(df, ["Île-de-France"], "2021-01-01", "2021-01-10")
    assert (filtered["Région"] == "Île-de-France").all()
    assert filtered["Date"].max() <= pd.Timestamp("2021-01-10")


def test_compute_kpis_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert kpis["total_consumption"] == 0.0
    assert kpis["dominant_source"] == "N/A"


def test_compute_kpis_nonempty():
    df = make_df()
    df["Production (MW)"] = df[[
        "Thermique (MW)", "Nucléaire (MW)", "Eolien (MW)", "Solaire (MW)",
        "Hydraulique (MW)", "Pompage (MW)", "Bioénergies (MW)",
    ]].sum(axis=1)
    kpis = d.compute_kpis(df)
    assert kpis["total_consumption"] > 0
    assert kpis["dominant_source"] == "Nucléaire"


def test_consumption_by_region():
    df = make_df()
    result = d.consumption_by_region(df)
    assert set(result.index) == {"Île-de-France", "Nouvelle-Aquitaine"}


def test_production_mix():
    df = make_df()
    result = d.production_mix(df)
    assert "Nucléaire" in result.index


def test_fit_regression_enough_data():
    df = make_df()
    result = d.fit_regression(df)
    assert result is not None
    assert result["rmse"] >= 0
    assert result["r2"] <= 1.0


def test_fit_regression_insufficient_data():
    df = make_df().iloc[:5]
    assert d.fit_regression(df) is None


def test_fit_forecast_insufficient_data():
    df = make_df()
    assert d.fit_forecast(df, "Île-de-France") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard
mkdir -p tests
pip install pandas numpy scikit-learn statsmodels pytest
pytest tests/ -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`.

- [ ] **Step 3: Write the implementation**

```python
# projects/energy-consumption-dashboard/data.py
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.tsa.statespace.sarimax import SARIMAX

PRODUCTION_COLUMNS = [
    "Thermique (MW)", "Nucléaire (MW)", "Eolien (MW)", "Solaire (MW)",
    "Hydraulique (MW)", "Pompage (MW)", "Bioénergies (MW)",
]
TCO_COLUMNS = [
    "TCO Thermique (%)", "TCO Nucléaire (%)", "TCO Eolien (%)",
    "TCO Hydraulique (%)", "TCO Solaire (%)", "TCO Bioénergies (%)",
]


def load_data(path="data/eco2mix_sample.csv"):
    df = pd.read_csv(path, sep=";")
    for col in PRODUCTION_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Consommation (MW)"] = pd.to_numeric(df["Consommation (MW)"], errors="coerce").fillna(0)
    for col in TCO_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Production (MW)"] = df[PRODUCTION_COLUMNS].sum(axis=1)
    return df


def filter_data(df, regions, start_date, end_date):
    mask = (
        df["Région"].isin(regions)
        & (df["Date"] >= pd.Timestamp(start_date))
        & (df["Date"] <= pd.Timestamp(end_date))
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {
            "total_consumption": 0.0,
            "total_production": 0.0,
            "avg_daily_consumption": 0.0,
            "dominant_source": "N/A",
        }
    mix = df[PRODUCTION_COLUMNS].sum()
    return {
        "total_consumption": float(df["Consommation (MW)"].sum()),
        "total_production": float(df["Production (MW)"].sum()) if "Production (MW)" in df.columns else float(mix.sum()),
        "avg_daily_consumption": float(df.groupby(df["Date"].dt.date)["Consommation (MW)"].sum().mean()),
        "dominant_source": mix.idxmax().replace(" (MW)", ""),
    }


def consumption_by_region(df):
    return df.groupby("Région")["Consommation (MW)"].sum().sort_values(ascending=False)


def production_mix(df):
    mix = df[PRODUCTION_COLUMNS].sum()
    mix.index = [c.replace(" (MW)", "") for c in mix.index]
    return mix


def production_over_time(df):
    daily = df.groupby(df["Date"].dt.date)[["Production (MW)", "Consommation (MW)"]].sum()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.reset_index().rename(columns={"index": "Date"})
    return daily


def fit_regression(df):
    feature_cols = [c for c in PRODUCTION_COLUMNS + TCO_COLUMNS if c in df.columns]
    data = df.dropna(subset=feature_cols + ["Consommation (MW)"])
    if len(data) < 10:
        return None
    X = data[feature_cols]
    y = data["Consommation (MW)"]
    split = max(int(len(data) * 0.8), 1)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    if len(X_test) == 0:
        X_test, y_test = X_train, y_train
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))
    return {"y_test": y_test.values, "y_pred": y_pred, "rmse": rmse, "r2": r2}


def fit_forecast(df, region, periods=12):
    region_df = (
        df[df["Région"] == region]
        .groupby(df["Date"].dt.to_period("M"))["Consommation (MW)"]
        .sum()
    )
    if len(region_df) < 24:
        return None
    region_df.index = region_df.index.to_timestamp()
    model = SARIMAX(
        region_df,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    results = model.fit(disp=False)
    forecast = results.get_forecast(steps=periods)
    forecast_index = pd.date_range(start=region_df.index[-1], periods=periods + 1, freq="MS")[1:]
    forecast_df = pd.DataFrame({"Date": forecast_index, "Forecast (MW)": forecast.predicted_mean.values})
    history_df = region_df.reset_index()
    history_df.columns = ["Date", "Consommation (MW)"]
    return {"history": history_df, "forecast": forecast_df}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add data.py tests/test_data.py
git commit -m "Add data module and tests for energy-consumption-dashboard"
```

---

## Task 3: energy-consumption-dashboard — Streamlit app + packaging

**Files:**
- Create: `projects/energy-consumption-dashboard/app.py`
- Create: `projects/energy-consumption-dashboard/requirements.txt`
- Create: `projects/energy-consumption-dashboard/README.md`
- Create: `projects/energy-consumption-dashboard/.github/workflows/streamlit.yml`

**Interfaces:**
- Consumes: all functions from Task 2's `data.py`

- [ ] **Step 1: Write app.py**

```python
# projects/energy-consumption-dashboard/app.py
import streamlit as st
import plotly.express as px
import pandas as pd

import data as d

st.set_page_config(page_title="Energy Consumption Dashboard", layout="wide")
st.title("France Energy Consumption & Production Dashboard")
st.caption(
    "Sample of the public RTE éCO2mix regional dataset (3 regions, 2021+). "
    "Full dataset: https://www.rte-france.com/eco2mix"
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

regions = sorted(df["Région"].unique())
min_date, max_date = df["Date"].min().date(), df["Date"].max().date()

st.sidebar.header("Filters")
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
date_range = st.sidebar.slider(
    "Date range", min_value=min_date, max_value=max_date, value=(min_date, max_date)
)

filtered = d.filter_data(df, selected_regions, date_range[0], date_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Consumption (MW)", f"{kpis['total_consumption']:,.0f}")
col2.metric("Total Production (MW)", f"{kpis['total_production']:,.0f}")
col3.metric("Avg Daily Consumption (MW)", f"{kpis['avg_daily_consumption']:,.0f}")
col4.metric("Dominant Source", kpis["dominant_source"])

st.subheader("Consumption by Region")
region_series = d.consumption_by_region(filtered)
st.plotly_chart(px.bar(region_series, labels={"value": "Consommation (MW)", "index": "Région"}), use_container_width=True)

st.subheader("Production Mix")
mix_series = d.production_mix(filtered)
st.plotly_chart(px.pie(values=mix_series.values, names=mix_series.index), use_container_width=True)

st.subheader("Production & Consumption Over Time")
trend_df = d.production_over_time(filtered)
fig = px.line(trend_df, x="Date", y=["Production (MW)", "Consommation (MW)"])
st.plotly_chart(fig, use_container_width=True)

st.subheader("Linear Regression: Predicting Consumption")
reg_result = d.fit_regression(filtered)
if reg_result is None:
    st.info("Not enough data in the current filter selection to fit a regression model.")
else:
    reg_col1, reg_col2 = st.columns(2)
    reg_col1.metric("RMSE", f"{reg_result['rmse']:,.1f}")
    reg_col2.metric("R²", f"{reg_result['r2']:.3f}")
    scatter_df = pd.DataFrame({"Actual": reg_result["y_test"], "Predicted": reg_result["y_pred"]})
    st.plotly_chart(px.scatter(scatter_df, x="Actual", y="Predicted"), use_container_width=True)

st.subheader("SARIMAX Forecast")
forecast_region = st.selectbox("Region to forecast", selected_regions)
if st.button("Run forecast"):
    with st.spinner("Fitting SARIMAX model..."):
        forecast_result = d.fit_forecast(filtered, forecast_region)
    if forecast_result is None:
        st.info("Not enough monthly history for this region/date range to forecast (need 24+ months).")
    else:
        hist = forecast_result["history"].rename(columns={"Consommation (MW)": "Value"})
        hist["Series"] = "Historical"
        fut = forecast_result["forecast"].rename(columns={"Forecast (MW)": "Value"})
        fut["Series"] = "Forecast"
        combined = pd.concat([hist, fut])
        st.plotly_chart(px.line(combined, x="Date", y="Value", color="Series"), use_container_width=True)

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="energy_consumption_filtered.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.30
pandas>=2
plotly>=5
scikit-learn
statsmodels
pytest
```

- [ ] **Step 3: Write README.md**

```markdown
# Energy Consumption Dashboard

Interactive Streamlit dashboard for exploring French national grid (RTE éCO2mix)
regional energy consumption and production data: consumption by region, energy
production mix, trends over time, a linear regression model predicting
consumption from the production mix, and an on-demand SARIMAX forecast.

Bundled data is a trimmed sample (3 regions, 2021+) of the full public
[RTE éCO2mix](https://www.rte-france.com/eco2mix) dataset, sized to fit
comfortably in git and Streamlit Community Cloud's free tier.

## Run locally

\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

- [ ] **Step 4: Write the CI workflow (from Task 1's template)**

```yaml
# projects/energy-consumption-dashboard/.github/workflows/streamlit.yml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/energy-consumption-dashboard/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/energy-consumption-dashboard
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Manually verify the app boots**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard
streamlit run app.py --server.headless true &
sleep 8
curl --fail http://localhost:8501/_stcore/health
kill %1
```

Expected: `curl` succeeds (no error), no traceback printed by the backgrounded `streamlit run` process. Manually click through region/date filters, the forecast button, and the download button once in a real browser (`streamlit run app.py` without `--server.headless`) to confirm rendering.

- [ ] **Step 6: Commit**

```bash
git add app.py requirements.txt README.md .github/workflows/streamlit.yml
git commit -m "Add Streamlit app for energy-consumption-dashboard"
```

---

## Task 4: ecommerce-income-dashboard — data module + tests

**Files:**
- Create: `projects/ecommerce-income-dashboard/data.py`
- Create: `projects/ecommerce-income-dashboard/data/E-commerce.csv` (copied)
- Test: `projects/ecommerce-income-dashboard/tests/test_data.py`

**Interfaces:**
- Produces: `load_data(path) -> pd.DataFrame`, `filter_data(df, genders, locations) -> pd.DataFrame`, `compute_kpis(df) -> dict`, `income_by_gender(df) -> pd.Series`, `sorted_income(df) -> pd.Series`

- [ ] **Step 1: Copy the source data**

```bash
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/ecommerce-income-dashboard/data
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/ecommerce-income-dashboard/tests
cp /Users/amine_jalili/Desktop/test/data-analysis-portfolio/ecommerce-income-analysis/E-commerce.csv \
   /Users/amine_jalili/Desktop/test/streamlit-projects/projects/ecommerce-income-dashboard/data/E-commerce.csv
```

- [ ] **Step 2: Write the failing tests**

```python
# projects/ecommerce-income-dashboard/tests/test_data.py
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_df():
    return pd.DataFrame({
        "Customer ID": [1, 2, 3, 4],
        "Age": [25, 30, 40, 22],
        "Gender": ["Female", "Male", "Female", "Male"],
        "Location": ["City A", "City B", "City A", "City B"],
        "Annual Income": [40000, 60000, 50000, 30000],
    })


def test_load_data(tmp_path):
    df = make_df()
    csv_path = tmp_path / "e.csv"
    df.to_csv(csv_path, index=False)
    loaded = d.load_data(str(csv_path))
    assert pd.api.types.is_numeric_dtype(loaded["Annual Income"])


def test_filter_data():
    df = make_df()
    filtered = d.filter_data(df, ["Female"], ["City A"])
    assert len(filtered) == 2
    assert (filtered["Gender"] == "Female").all()


def test_compute_kpis_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert kpis["customer_count"] == 0


def test_compute_kpis_nonempty():
    kpis = d.compute_kpis(make_df())
    assert kpis["customer_count"] == 4
    assert kpis["avg_income"] == 45000.0


def test_income_by_gender():
    result = d.income_by_gender(make_df())
    assert result["Female"] == 90000
    assert result["Male"] == 90000


def test_sorted_income():
    result = d.sorted_income(make_df())
    assert list(result) == [30000, 40000, 50000, 60000]
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/ecommerce-income-dashboard
pip install pandas pytest
pytest tests/ -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`.

- [ ] **Step 4: Write the implementation**

```python
# projects/ecommerce-income-dashboard/data.py
import pandas as pd


def load_data(path="data/E-commerce.csv"):
    df = pd.read_csv(path)
    df["Annual Income"] = pd.to_numeric(df["Annual Income"], errors="coerce")
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    return df


def filter_data(df, genders, locations):
    mask = df["Gender"].isin(genders) & df["Location"].isin(locations)
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"avg_income": 0.0, "median_income": 0.0, "customer_count": 0}
    return {
        "avg_income": float(df["Annual Income"].mean()),
        "median_income": float(df["Annual Income"].median()),
        "customer_count": int(len(df)),
    }


def income_by_gender(df):
    return df.groupby("Gender")["Annual Income"].sum().sort_values(ascending=False)


def sorted_income(df):
    return df["Annual Income"].dropna().sort_values().reset_index(drop=True)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add data.py data/E-commerce.csv tests/test_data.py
git commit -m "Add data module, tests, and bundled data for ecommerce-income-dashboard"
```

---

## Task 5: ecommerce-income-dashboard — Streamlit app + packaging

**Files:**
- Create: `projects/ecommerce-income-dashboard/app.py`
- Create: `projects/ecommerce-income-dashboard/requirements.txt`
- Create: `projects/ecommerce-income-dashboard/README.md`
- Create: `projects/ecommerce-income-dashboard/.github/workflows/streamlit.yml`

**Interfaces:**
- Consumes: all functions from Task 4's `data.py`

- [ ] **Step 1: Write app.py**

```python
# projects/ecommerce-income-dashboard/app.py
import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="E-commerce Income Dashboard", layout="wide")
st.title("E-commerce Customer Income Dashboard")
st.caption("Synthetic e-commerce customer dataset — not real customer data.")


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

genders = sorted(df["Gender"].dropna().unique())
locations = sorted(df["Location"].dropna().unique())

st.sidebar.header("Filters")
selected_genders = st.sidebar.multiselect("Gender", genders, default=genders)
selected_locations = st.sidebar.multiselect("Location", locations, default=locations)

filtered = d.filter_data(df, selected_genders, selected_locations)

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Avg Annual Income", f"${kpis['avg_income']:,.0f}")
col2.metric("Median Annual Income", f"${kpis['median_income']:,.0f}")
col3.metric("Customers", kpis["customer_count"])

st.subheader("Total Annual Income by Gender")
income_series = d.income_by_gender(filtered)
st.plotly_chart(px.bar(income_series, orientation="h"), use_container_width=True)

st.subheader("Annual Income Distribution (sorted)")
sorted_series = d.sorted_income(filtered)
st.plotly_chart(px.scatter(x=sorted_series.index, y=sorted_series.values, labels={"x": "Index", "y": "Annual Income"}), use_container_width=True)

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="ecommerce_filtered.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.30
pandas>=2
plotly>=5
pytest
```

- [ ] **Step 3: Write README.md**

```markdown
# E-commerce Income Dashboard

Interactive Streamlit dashboard for a synthetic e-commerce customer dataset:
income by gender, income distribution, filterable by gender and location.

Data is fabricated/synthetic — not real customer data.

## Run locally

\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

- [ ] **Step 4: Write the CI workflow**

```yaml
# projects/ecommerce-income-dashboard/.github/workflows/streamlit.yml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/ecommerce-income-dashboard/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/ecommerce-income-dashboard
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Manually verify the app boots**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/ecommerce-income-dashboard
streamlit run app.py --server.headless true &
sleep 8
curl --fail http://localhost:8501/_stcore/health
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add app.py requirements.txt README.md .github/workflows/streamlit.yml
git commit -m "Add Streamlit app for ecommerce-income-dashboard"
```

---

## Task 6: finance-transaction-dashboard — data module + tests

**Files:**
- Create: `projects/finance-transaction-dashboard/data.py`
- Create: `projects/finance-transaction-dashboard/data/FInance_cleaned.csv` (copied)
- Test: `projects/finance-transaction-dashboard/tests/test_data.py`

**Interfaces:**
- Produces: `load_data(path) -> pd.DataFrame`, `filter_data(df, categories, start_month, end_month) -> pd.DataFrame`, `compute_kpis(df) -> dict`, `monthly_credit_debit(df) -> pd.DataFrame`, `category_breakdown(df) -> pd.DataFrame`

- [ ] **Step 1: Copy the source data**

```bash
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/finance-transaction-dashboard/data
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/finance-transaction-dashboard/tests
cp /Users/amine_jalili/Desktop/test/data-analysis-portfolio/finance-transaction-cleaning/FInance_cleaned.csv \
   /Users/amine_jalili/Desktop/test/streamlit-projects/projects/finance-transaction-dashboard/data/FInance_cleaned.csv
```

- [ ] **Step 2: Write the failing tests**

```python
# projects/finance-transaction-dashboard/tests/test_data.py
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_df():
    return pd.DataFrame({
        "Date operatio valeur": ["2024-01-01", "2024-01-15", "2024-02-01"],
        "Date": ["2024-01-01", "2024-01-15", "2024-02-01"],
        "libelle des operations": ["Salary #1", "Grocery #2", "Salary #3"],
        "Débit": [0.0, 50.0, 0.0],
        "Crédit": [2000.0, 0.0, 2100.0],
        "Category Improved": ["Salary", "Other", "Salary"],
        "YearMonth": ["2024-01", "2024-01", "2024-02"],
    })


def test_load_data(tmp_path):
    df = make_df()
    csv_path = tmp_path / "f.csv"
    df.to_csv(csv_path, sep=";", index=False)
    loaded = d.load_data(str(csv_path))
    assert "Category" in loaded.columns
    assert pd.api.types.is_numeric_dtype(loaded["Débit"])


def test_filter_data():
    df = make_df().rename(columns={"Category Improved": "Category"})
    filtered = d.filter_data(df, ["Salary"], "2024-01", "2024-02")
    assert len(filtered) == 2


def test_compute_kpis_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert kpis["transaction_count"] == 0


def test_compute_kpis_nonempty():
    df = make_df().rename(columns={"Category Improved": "Category"})
    kpis = d.compute_kpis(df)
    assert kpis["total_credit"] == 4100.0
    assert kpis["total_debit"] == 50.0
    assert kpis["net"] == 4050.0


def test_monthly_credit_debit():
    df = make_df().rename(columns={"Category Improved": "Category"})
    result = d.monthly_credit_debit(df)
    assert set(result["YearMonth"]) == {"2024-01", "2024-02"}


def test_category_breakdown():
    df = make_df().rename(columns={"Category Improved": "Category"})
    result = d.category_breakdown(df)
    assert result.loc["Salary", "Crédit"] == 4100.0
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/finance-transaction-dashboard
pip install pandas pytest
pytest tests/ -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`.

- [ ] **Step 4: Write the implementation**

```python
# projects/finance-transaction-dashboard/data.py
import pandas as pd


def load_data(path="data/FInance_cleaned.csv"):
    df = pd.read_csv(path, sep=";")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Débit"] = pd.to_numeric(df["Débit"], errors="coerce").fillna(0)
    df["Crédit"] = pd.to_numeric(df["Crédit"], errors="coerce").fillna(0)
    df = df.rename(columns={"Category Improved": "Category"})
    return df


def filter_data(df, categories, start_month, end_month):
    mask = (
        df["Category"].isin(categories)
        & (df["YearMonth"] >= start_month)
        & (df["YearMonth"] <= end_month)
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"total_debit": 0.0, "total_credit": 0.0, "net": 0.0, "transaction_count": 0}
    total_debit = float(df["Débit"].sum())
    total_credit = float(df["Crédit"].sum())
    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net": total_credit - total_debit,
        "transaction_count": int(len(df)),
    }


def monthly_credit_debit(df):
    return df.groupby("YearMonth")[["Débit", "Crédit"]].sum().reset_index().sort_values("YearMonth")


def category_breakdown(df):
    return df.groupby("Category")[["Débit", "Crédit"]].sum()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add data.py data/FInance_cleaned.csv tests/test_data.py
git commit -m "Add data module, tests, and bundled data for finance-transaction-dashboard"
```

---

## Task 7: finance-transaction-dashboard — Streamlit app + packaging

**Files:**
- Create: `projects/finance-transaction-dashboard/app.py`
- Create: `projects/finance-transaction-dashboard/requirements.txt`
- Create: `projects/finance-transaction-dashboard/README.md`
- Create: `projects/finance-transaction-dashboard/.github/workflows/streamlit.yml`

**Interfaces:**
- Consumes: all functions from Task 6's `data.py`

- [ ] **Step 1: Write app.py**

```python
# projects/finance-transaction-dashboard/app.py
import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Finance Transaction Dashboard", layout="wide")
st.title("Personal Finance Transaction Dashboard")
st.caption("All amounts and merchant descriptions are anonymized/randomized — not real transactions.")


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

categories = sorted(df["Category"].dropna().unique())
months = sorted(df["YearMonth"].dropna().unique())

st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
month_range = st.sidebar.select_slider("Month range", options=months, value=(months[0], months[-1]))

filtered = d.filter_data(df, selected_categories, month_range[0], month_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Crédit", f"{kpis['total_credit']:,.2f}")
col2.metric("Total Débit", f"{kpis['total_debit']:,.2f}")
col3.metric("Net", f"{kpis['net']:,.2f}")
col4.metric("Transactions", kpis["transaction_count"])

st.subheader("Monthly Crédit vs Débit")
monthly = d.monthly_credit_debit(filtered)
st.plotly_chart(px.line(monthly, x="YearMonth", y=["Débit", "Crédit"]), use_container_width=True)

st.subheader("Category Breakdown")
breakdown = d.category_breakdown(filtered).reset_index()
st.plotly_chart(px.bar(breakdown, x="Category", y=["Débit", "Crédit"], barmode="group"), use_container_width=True)

st.subheader("Filtered Transactions")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="finance_transactions_filtered.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.30
pandas>=2
plotly>=5
pytest
```

- [ ] **Step 3: Write README.md**

```markdown
# Finance Transaction Dashboard

Interactive Streamlit dashboard for categorized bank-transaction data: monthly
credit/debit trends and category breakdowns, filterable by category and month.

All monetary amounts and merchant descriptions are anonymized/randomized —
not real transaction data.

## Run locally

\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

- [ ] **Step 4: Write the CI workflow**

```yaml
# projects/finance-transaction-dashboard/.github/workflows/streamlit.yml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/finance-transaction-dashboard/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/finance-transaction-dashboard
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Manually verify the app boots**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/finance-transaction-dashboard
streamlit run app.py --server.headless true &
sleep 8
curl --fail http://localhost:8501/_stcore/health
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add app.py requirements.txt README.md .github/workflows/streamlit.yml
git commit -m "Add Streamlit app for finance-transaction-dashboard"
```

---

## Task 8: budget-cashflow-dashboard — data module + tests

**Data source decision:** this app uses `fichiers.csv` only (clean tidy category-by-month format). `budgetting2023.csv` and `oct24.csv` are not bundled — `budgetting2023.csv` has fragile unescaped-comma rows from the original spreadsheet export, and `oct24.csv` is transaction-level data already covered by the same pattern as `finance-transaction-dashboard`/`france-bank-transactions-dashboard`.

**Files:**
- Create: `projects/budget-cashflow-dashboard/data.py`
- Create: `projects/budget-cashflow-dashboard/data/fichiers.csv` (copied)
- Test: `projects/budget-cashflow-dashboard/tests/test_data.py`

**Interfaces:**
- Produces: `load_data(path) -> pd.DataFrame` (long format: Category, MonthLabel, Amount, Month), `filter_data(df, categories, start_month, end_month) -> pd.DataFrame`, `cashflow_categories(df) -> list`, `expense_categories(df) -> list`, `compute_kpis(df) -> dict`, `cashflow_by_category_over_time(df) -> pd.DataFrame`, `expense_breakdown(df) -> pd.Series`, `net_worth_trend(df) -> pd.DataFrame`

- [ ] **Step 1: Copy the source data**

```bash
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/budget-cashflow-dashboard/data
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/budget-cashflow-dashboard/tests
cp /Users/amine_jalili/Desktop/test/data-analysis-portfolio/budget-cashflow-tracker/fichiers.csv \
   /Users/amine_jalili/Desktop/test/streamlit-projects/projects/budget-cashflow-dashboard/data/fichiers.csv
```

- [ ] **Step 2: Write the failing tests**

```python
# projects/budget-cashflow-dashboard/tests/test_data.py
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_csv(tmp_path):
    content = (
        "Category,2023-Janvier,2023-Février\n"
        "CASHFLOW_LAVORO,1000.00,1200.00\n"
        "Affitto,200.00,200.00\n"
        "Cibo Fuori,50.00,60.00\n"
        "SAFE KEEP,500.00,700.00\n"
    )
    path = tmp_path / "fichiers.csv"
    path.write_text(content)
    return str(path)


def test_load_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Month"])
    assert df["Amount"].notna().all()


def test_filter_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    filtered = d.filter_data(df, ["CASHFLOW_LAVORO"], "2023-01-01", "2023-01-31")
    assert len(filtered) == 1
    assert filtered.iloc[0]["Amount"] == 1000.00


def test_cashflow_categories(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert d.cashflow_categories(df) == ["CASHFLOW_LAVORO"]


def test_expense_categories(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert set(d.expense_categories(df)) == {"Affitto", "Cibo Fuori"}


def test_compute_kpis(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    assert kpis["total_cashflow"] == 2200.00
    assert kpis["total_expenses"] == 510.00


def test_cashflow_by_category_over_time(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.cashflow_by_category_over_time(df)
    assert set(result["Category"]) == {"CASHFLOW_LAVORO"}


def test_expense_breakdown(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.expense_breakdown(df)
    assert result["Affitto"] == 400.00


def test_net_worth_trend(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.net_worth_trend(df)
    assert len(result) == 2
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/budget-cashflow-dashboard
pip install pandas pytest
pytest tests/ -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`.

- [ ] **Step 4: Write the implementation**

```python
# projects/budget-cashflow-dashboard/data.py
import pandas as pd

FRENCH_MONTHS = {
    "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6,
    "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12,
}

CASHFLOW_PREFIX = "CASHFLOW_"
EXPENSE_CATEGORIES = [
    "Affitto", "Cibo Fuori", "Spesa", "Regali", "Investimento", "Coiffeur",
    "Divertimento", "Abbonamenti", "Luce", "Treno", "Vestiti",
]
NET_WORTH_CATEGORY = "SAFE KEEP"


def _parse_month_column(col):
    year_str, month_str = col.split("-")
    return pd.Timestamp(year=int(year_str), month=FRENCH_MONTHS[month_str], day=1)


def load_data(path="data/fichiers.csv"):
    df = pd.read_csv(path)
    month_cols = [c for c in df.columns if c != "Category"]
    long_df = df.melt(id_vars="Category", value_vars=month_cols, var_name="MonthLabel", value_name="Amount")
    long_df["Amount"] = pd.to_numeric(long_df["Amount"], errors="coerce")
    long_df = long_df.dropna(subset=["Amount"])
    long_df["Month"] = long_df["MonthLabel"].apply(_parse_month_column)
    return long_df


def filter_data(df, categories, start_month, end_month):
    mask = (
        df["Category"].isin(categories)
        & (df["Month"] >= pd.Timestamp(start_month))
        & (df["Month"] <= pd.Timestamp(end_month))
    )
    return df[mask]


def cashflow_categories(df):
    return sorted(c for c in df["Category"].unique() if c.startswith(CASHFLOW_PREFIX))


def expense_categories(df):
    return sorted(c for c in df["Category"].unique() if c in EXPENSE_CATEGORIES)


def compute_kpis(df):
    cashflow_df = df[df["Category"].str.startswith(CASHFLOW_PREFIX)]
    expense_df = df[df["Category"].isin(EXPENSE_CATEGORIES)]
    if df.empty:
        return {"total_cashflow": 0.0, "total_expenses": 0.0, "avg_monthly_cashflow": 0.0}
    total_cashflow = float(cashflow_df["Amount"].sum())
    total_expenses = float(expense_df["Amount"].sum())
    avg_monthly = float(cashflow_df.groupby("Month")["Amount"].sum().mean()) if not cashflow_df.empty else 0.0
    return {
        "total_cashflow": total_cashflow,
        "total_expenses": total_expenses,
        "avg_monthly_cashflow": avg_monthly,
    }


def cashflow_by_category_over_time(df):
    cashflow_df = df[df["Category"].str.startswith(CASHFLOW_PREFIX)]
    return cashflow_df.groupby(["Month", "Category"])["Amount"].sum().reset_index()


def expense_breakdown(df):
    expense_df = df[df["Category"].isin(EXPENSE_CATEGORIES)]
    return expense_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)


def net_worth_trend(df):
    net_worth_df = df[df["Category"] == NET_WORTH_CATEGORY]
    return net_worth_df.groupby("Month")["Amount"].sum().reset_index().sort_values("Month")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add data.py data/fichiers.csv tests/test_data.py
git commit -m "Add data module, tests, and bundled data for budget-cashflow-dashboard"
```

---

## Task 9: budget-cashflow-dashboard — Streamlit app + packaging

**Files:**
- Create: `projects/budget-cashflow-dashboard/app.py`
- Create: `projects/budget-cashflow-dashboard/requirements.txt`
- Create: `projects/budget-cashflow-dashboard/README.md`
- Create: `projects/budget-cashflow-dashboard/.github/workflows/streamlit.yml`

**Interfaces:**
- Consumes: all functions from Task 8's `data.py`

- [ ] **Step 1: Write app.py**

```python
# projects/budget-cashflow-dashboard/app.py
import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Budget & Cash Flow Dashboard", layout="wide")
st.title("Personal Budget & Cash Flow Dashboard")
st.caption("All monetary values are anonymized/randomized — not real financial data.")


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

all_categories = d.cashflow_categories(df) + d.expense_categories(df)
months = sorted(df["Month"].unique())

st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Category", all_categories, default=all_categories)
month_range = st.sidebar.select_slider(
    "Month range",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda m: m.strftime("%Y-%m"),
)

filtered = d.filter_data(df, selected_categories, month_range[0], month_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Total Cash Flow", f"{kpis['total_cashflow']:,.2f}")
col2.metric("Total Expenses", f"{kpis['total_expenses']:,.2f}")
col3.metric("Avg Monthly Cash Flow", f"{kpis['avg_monthly_cashflow']:,.2f}")

st.subheader("Cash Flow by Category Over Time")
cashflow_trend = d.cashflow_by_category_over_time(filtered)
if cashflow_trend.empty:
    st.info("No cash flow categories selected.")
else:
    st.plotly_chart(px.line(cashflow_trend, x="Month", y="Amount", color="Category"), use_container_width=True)

st.subheader("Expense Breakdown")
expenses = d.expense_breakdown(filtered)
if expenses.empty:
    st.info("No expense categories selected.")
else:
    st.plotly_chart(px.bar(expenses), use_container_width=True)

st.subheader("Net Worth Trend (Safe Keep)")
net_worth = d.net_worth_trend(filtered)
if net_worth.empty:
    st.info("Net worth category not in the current filter selection.")
else:
    st.plotly_chart(px.line(net_worth, x="Month", y="Amount"), use_container_width=True)

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="budget_cashflow_filtered.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.30
pandas>=2
plotly>=5
pytest
```

- [ ] **Step 3: Write README.md**

```markdown
# Budget & Cash Flow Dashboard

Interactive Streamlit dashboard for monthly cash flow by income category,
expense breakdown, and a net-worth ("safe keep" savings) trend, filterable by
category and month range.

Built from `fichiers.csv` (the tidy category-by-month cash flow export). All
monetary values are anonymized/randomized — not real financial data.

## Run locally

\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

- [ ] **Step 4: Write the CI workflow**

```yaml
# projects/budget-cashflow-dashboard/.github/workflows/streamlit.yml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/budget-cashflow-dashboard/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/budget-cashflow-dashboard
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Manually verify the app boots**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/budget-cashflow-dashboard
streamlit run app.py --server.headless true &
sleep 8
curl --fail http://localhost:8501/_stcore/health
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add app.py requirements.txt README.md .github/workflows/streamlit.yml
git commit -m "Add Streamlit app for budget-cashflow-dashboard"
```

---

## Task 10: france-bank-transactions-dashboard — data module + tests

**Files:**
- Create: `projects/france-bank-transactions-dashboard/data.py`
- Create: `projects/france-bank-transactions-dashboard/data/filtered_data_fixed.csv` (copied)
- Test: `projects/france-bank-transactions-dashboard/tests/test_data.py`

**Interfaces:**
- Produces: `categorize(label) -> str`, `load_data(path) -> pd.DataFrame`, `filter_data(df, categories, months) -> pd.DataFrame`, `compute_kpis(df) -> dict`, `category_breakdown(df) -> pd.DataFrame`, `largest_transactions(df, n=10) -> pd.DataFrame`

- [ ] **Step 1: Copy the source data**

```bash
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/france-bank-transactions-dashboard/data
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/france-bank-transactions-dashboard/tests
cp /Users/amine_jalili/Desktop/test/data-analysis-portfolio/france-bank-transactions/filtered_data_fixed.csv \
   /Users/amine_jalili/Desktop/test/streamlit-projects/projects/france-bank-transactions-dashboard/data/filtered_data_fixed.csv
```

- [ ] **Step 2: Write the failing tests**

```python
# projects/france-bank-transactions-dashboard/tests/test_data.py
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_csv(tmp_path):
    content = (
        "Date opé.;Date valeur;Libellé des opérations;Débit;Crédit;\n"
        "9.07;9.07;Carte X1234 Grocery Market B;10.0;;\n"
        "9.07;9.07;Virement Employer Payroll Salaire;;2000.0;\n"
        "10.08;10.08;Carte X1234 Pharmacy D;20.0;;\n"
    )
    path = tmp_path / "f.csv"
    path.write_text(content)
    return str(path)


def test_categorize():
    assert d.categorize("Carte X1234 Grocery Market B") == "Groceries"
    assert d.categorize("Virement Employer Payroll Salaire") == "Salary"
    assert d.categorize("Something Unknown") == "Other"


def test_load_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert "Category" in df.columns
    assert "Month" in df.columns
    assert set(df["Month"]) == {7, 8}


def test_filter_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    filtered = d.filter_data(df, ["Groceries"], [7])
    assert len(filtered) == 1


def test_compute_kpis(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    assert kpis["total_credit"] == 2000.0
    assert kpis["total_debit"] == 30.0
    assert kpis["transaction_count"] == 3


def test_category_breakdown(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.category_breakdown(df)
    assert result.loc["Salary", "Crédit"] == 2000.0


def test_largest_transactions(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.largest_transactions(df, n=1)
    assert len(result) == 1
    assert result.iloc[0]["Category"] == "Salary"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/france-bank-transactions-dashboard
pip install pandas pytest
pytest tests/ -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`.

- [ ] **Step 4: Write the implementation**

```python
# projects/france-bank-transactions-dashboard/data.py
import pandas as pd

CATEGORY_RULES = [
    ("Salaire", "Salary"),
    ("Employer Payroll", "Salary"),
    ("Pharmacy", "Health"),
    ("Grocery Market", "Groceries"),
    ("Telecom Provider", "Utilities"),
    ("Utility Provider", "Utilities"),
    ("Coffee Shop", "Dining"),
    ("Retail Store", "Shopping"),
    ("Electronics Store", "Shopping"),
    ("Online Shop", "Shopping"),
    ("Transport Ticket", "Transport"),
    ("Agency Deposit", "Deposit"),
    ("Contact", "Transfer"),
    ("Frais Tenue de compte", "Fees"),
    ("solde", "Balance"),
    ("Total", "Balance"),
]


def categorize(label):
    for keyword, category in CATEGORY_RULES:
        if keyword.lower() in str(label).lower():
            return category
    return "Other"


def _month_of(date_str):
    parts = str(date_str).split(".")
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return None


def load_data(path="data/filtered_data_fixed.csv"):
    df = pd.read_csv(path, sep=";")
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    df["Débit"] = pd.to_numeric(df["Débit"], errors="coerce").fillna(0)
    df["Crédit"] = pd.to_numeric(df["Crédit"], errors="coerce").fillna(0)
    df["Category"] = df["Libellé des opérations"].apply(categorize)
    df["Month"] = df["Date opé."].apply(_month_of)
    df = df[df["Category"] != "Balance"]
    return df


def filter_data(df, categories, months):
    return df[df["Category"].isin(categories) & df["Month"].isin(months)]


def compute_kpis(df):
    if df.empty:
        return {"total_debit": 0.0, "total_credit": 0.0, "transaction_count": 0}
    return {
        "total_debit": float(df["Débit"].sum()),
        "total_credit": float(df["Crédit"].sum()),
        "transaction_count": int(len(df)),
    }


def category_breakdown(df):
    return df.groupby("Category")[["Débit", "Crédit"]].sum()


def largest_transactions(df, n=10):
    return (
        df.assign(Amount=df["Débit"] + df["Crédit"])
        .sort_values("Amount", ascending=False)
        .head(n)
    )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add data.py data/filtered_data_fixed.csv tests/test_data.py
git commit -m "Add data module, tests, and bundled data for france-bank-transactions-dashboard"
```

---

## Task 11: france-bank-transactions-dashboard — Streamlit app + packaging

**Files:**
- Create: `projects/france-bank-transactions-dashboard/app.py`
- Create: `projects/france-bank-transactions-dashboard/requirements.txt`
- Create: `projects/france-bank-transactions-dashboard/README.md`
- Create: `projects/france-bank-transactions-dashboard/.github/workflows/streamlit.yml`

**Interfaces:**
- Consumes: all functions from Task 10's `data.py`

- [ ] **Step 1: Write app.py**

```python
# projects/france-bank-transactions-dashboard/app.py
import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Bank Transactions Dashboard", layout="wide")
st.title("Bank Statement Transactions Dashboard")
st.caption("All amounts and merchant descriptions are anonymized/randomized — not real transactions.")


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

categories = sorted(df["Category"].dropna().unique())
months = sorted(df["Month"].dropna().unique())

st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
selected_months = st.sidebar.multiselect("Month", months, default=months)

filtered = d.filter_data(df, selected_categories, selected_months)

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Total Crédit", f"{kpis['total_credit']:,.2f}")
col2.metric("Total Débit", f"{kpis['total_debit']:,.2f}")
col3.metric("Transactions", kpis["transaction_count"])

st.subheader("Category Breakdown")
breakdown = d.category_breakdown(filtered).reset_index()
st.plotly_chart(px.bar(breakdown, x="Category", y=["Débit", "Crédit"], barmode="group"), use_container_width=True)

st.subheader("Largest Transactions")
largest = d.largest_transactions(filtered, n=10)
st.dataframe(largest)

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="bank_transactions_filtered.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.30
pandas>=2
plotly>=5
pytest
```

- [ ] **Step 3: Write README.md**

```markdown
# Bank Transactions Dashboard

Interactive Streamlit dashboard for bank-statement-derived transaction data:
category breakdown (categorized by merchant-description keyword matching),
largest transactions, filterable by category and month.

All amounts and merchant descriptions are anonymized/randomized — not real
transaction data.

## Run locally

\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

- [ ] **Step 4: Write the CI workflow**

```yaml
# projects/france-bank-transactions-dashboard/.github/workflows/streamlit.yml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/france-bank-transactions-dashboard/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/france-bank-transactions-dashboard
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Manually verify the app boots**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/france-bank-transactions-dashboard
streamlit run app.py --server.headless true &
sleep 8
curl --fail http://localhost:8501/_stcore/health
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add app.py requirements.txt README.md .github/workflows/streamlit.yml
git commit -m "Add Streamlit app for france-bank-transactions-dashboard"
```

---

## Task 12: luxembourg-rental-dashboard — data module + tests

**Files:**
- Create: `projects/luxembourg-rental-dashboard/data.py`
- Create: `projects/luxembourg-rental-dashboard/data/luxembourg_properties.csv` (copied)
- Test: `projects/luxembourg-rental-dashboard/tests/test_data.py`

**Interfaces:**
- Produces: `load_data(path) -> pd.DataFrame`, `filter_data(df, locations, price_range, surface_range) -> pd.DataFrame`, `compute_kpis(df) -> dict`, `listings_by_location(df) -> pd.Series`

- [ ] **Step 1: Copy the source data**

```bash
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/luxembourg-rental-dashboard/data
mkdir -p /Users/amine_jalili/Desktop/test/streamlit-projects/projects/luxembourg-rental-dashboard/tests
cp /Users/amine_jalili/Desktop/test/data-analysis-portfolio/luxembourg-rental-scraper/luxembourg_properties.csv \
   /Users/amine_jalili/Desktop/test/streamlit-projects/projects/luxembourg-rental-dashboard/data/luxembourg_properties.csv
```

- [ ] **Step 2: Write the failing tests**

```python
# projects/luxembourg-rental-dashboard/tests/test_data.py
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_csv(tmp_path):
    content = (
        "Price,Location,Surface\n"
        "1 200 €,Luxembourg-Centre,45 m²\n"
        "900 €,Luxembourg-Neudorf,29 m²\n"
        "not-a-price,Luxembourg-Gare,invalid\n"
    )
    path = tmp_path / "l.csv"
    path.write_text(content)
    return str(path)


def test_load_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert len(df) == 2
    assert df["Price"].tolist() == [1200.0, 900.0]
    assert df["Surface"].tolist() == [45.0, 29.0]


def test_filter_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    filtered = d.filter_data(df, ["Luxembourg-Centre"], (0, 2000), (0, 100))
    assert len(filtered) == 1


def test_compute_kpis_empty():
    kpis = d.compute_kpis(pd.DataFrame(columns=["Price", "Surface", "Location"]))
    assert kpis["listing_count"] == 0


def test_compute_kpis_nonempty(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    assert kpis["listing_count"] == 2
    assert kpis["avg_price"] == 1050.0


def test_listings_by_location(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.listings_by_location(df)
    assert result["Luxembourg-Centre"] == 1
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/luxembourg-rental-dashboard
pip install pandas pytest
pytest tests/ -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`.

- [ ] **Step 4: Write the implementation**

```python
# projects/luxembourg-rental-dashboard/data.py
import pandas as pd


def load_data(path="data/luxembourg_properties.csv"):
    df = pd.read_csv(path)
    df["Price"] = (
        df["Price"].astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=True)
        .str.replace(r"[^0-9.]", "", regex=True)
        .str.strip()
    )
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Surface"] = df["Surface"].astype(str).str.extract(r"(\d+)", expand=False)
    df["Surface"] = pd.to_numeric(df["Surface"], errors="coerce")
    return df.dropna(subset=["Price", "Surface"]).reset_index(drop=True)


def filter_data(df, locations, price_range, surface_range):
    mask = (
        df["Location"].isin(locations)
        & df["Price"].between(price_range[0], price_range[1])
        & df["Surface"].between(surface_range[0], surface_range[1])
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"avg_price": 0.0, "median_price": 0.0, "listing_count": 0, "avg_price_per_sqm": 0.0}
    price_per_sqm = (df["Price"] / df["Surface"]).replace([float("inf")], pd.NA).dropna()
    return {
        "avg_price": float(df["Price"].mean()),
        "median_price": float(df["Price"].median()),
        "listing_count": int(len(df)),
        "avg_price_per_sqm": float(price_per_sqm.mean()) if not price_per_sqm.empty else 0.0,
    }


def listings_by_location(df):
    return df["Location"].value_counts()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add data.py data/luxembourg_properties.csv tests/test_data.py
git commit -m "Add data module, tests, and bundled data for luxembourg-rental-dashboard"
```

---

## Task 13: luxembourg-rental-dashboard — Streamlit app + packaging

**Files:**
- Create: `projects/luxembourg-rental-dashboard/app.py`
- Create: `projects/luxembourg-rental-dashboard/requirements.txt`
- Create: `projects/luxembourg-rental-dashboard/README.md`
- Create: `projects/luxembourg-rental-dashboard/.github/workflows/streamlit.yml`

**Interfaces:**
- Consumes: all functions from Task 12's `data.py`

- [ ] **Step 1: Write app.py**

```python
# projects/luxembourg-rental-dashboard/app.py
import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Luxembourg Rental Dashboard", layout="wide")
st.title("Luxembourg Rental Listings Dashboard")
st.caption("Public rental listing data scraped from athome.lu — no owner/tenant personal data.")


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

locations = sorted(df["Location"].dropna().unique())
price_min, price_max = float(df["Price"].min()), float(df["Price"].max())
surface_min, surface_max = float(df["Surface"].min()), float(df["Surface"].max())

st.sidebar.header("Filters")
selected_locations = st.sidebar.multiselect("Location", locations, default=locations)
price_range = st.sidebar.slider("Price (€)", price_min, price_max, (price_min, price_max))
surface_range = st.sidebar.slider("Surface (m²)", surface_min, surface_max, (surface_min, surface_max))

filtered = d.filter_data(df, selected_locations, price_range, surface_range)

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Price", f"€{kpis['avg_price']:,.0f}")
col2.metric("Median Price", f"€{kpis['median_price']:,.0f}")
col3.metric("Listings", kpis["listing_count"])
col4.metric("Avg €/m²", f"€{kpis['avg_price_per_sqm']:,.1f}")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Price Distribution")
    st.plotly_chart(px.histogram(filtered, x="Price", nbins=20), use_container_width=True)
with col_b:
    st.subheader("Surface Distribution")
    st.plotly_chart(px.histogram(filtered, x="Surface", nbins=20), use_container_width=True)

st.subheader("Price vs Surface")
st.plotly_chart(px.scatter(filtered, x="Surface", y="Price", color="Location"), use_container_width=True)

st.subheader("Listings by Location")
location_counts = d.listings_by_location(filtered)
st.plotly_chart(px.bar(location_counts), use_container_width=True)

st.subheader("Filtered Listings")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="luxembourg_listings_filtered.csv",
    mime="text/csv",
)
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.30
pandas>=2
plotly>=5
pytest
```

- [ ] **Step 3: Write README.md**

```markdown
# Luxembourg Rental Dashboard

Interactive Streamlit dashboard for Luxembourg rental listing data: price and
surface distributions, price-vs-surface scatter, and listing counts by
location, filterable by location, price range, and surface range.

Data is public listing information scraped from athome.lu — no owner or
tenant personal data is included.

## Run locally

\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

- [ ] **Step 4: Write the CI workflow**

```yaml
# projects/luxembourg-rental-dashboard/.github/workflows/streamlit.yml
name: Streamlit Smoke Test

on:
  push:
    branches: [main]
    paths:
      - 'projects/luxembourg-rental-dashboard/**'

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/luxembourg-rental-dashboard
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - name: Headless boot smoke test
        run: |
          streamlit run app.py --server.headless true &
          sleep 8
          curl --fail http://localhost:8501/_stcore/health
```

- [ ] **Step 5: Manually verify the app boots**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects/projects/luxembourg-rental-dashboard
streamlit run app.py --server.headless true &
sleep 8
curl --fail http://localhost:8501/_stcore/health
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add app.py requirements.txt README.md .github/workflows/streamlit.yml
git commit -m "Add Streamlit app for luxembourg-rental-dashboard"
```

---

## Task 14: Top-level streamlit-projects README index

**Files:**
- Modify: `/Users/amine_jalili/Desktop/test/streamlit-projects/README.md`

**Interfaces:**
- Consumes: nothing (documentation only)

- [ ] **Step 1: Update the README**

```markdown
# Streamlit Projects

A collection of interactive Streamlit dashboards.

## Projects

| App | Description |
|---|---|
| [energy-consumption-dashboard](./projects/energy-consumption-dashboard) | French national grid (RTE éCO2mix) energy consumption/production explorer, with regression and SARIMAX forecasting |
| [ecommerce-income-dashboard](./projects/ecommerce-income-dashboard) | Synthetic e-commerce customer income explorer |
| [finance-transaction-dashboard](./projects/finance-transaction-dashboard) | Categorized bank-transaction trends (anonymized data) |
| [budget-cashflow-dashboard](./projects/budget-cashflow-dashboard) | Monthly budget, expenses, and net-worth tracker (anonymized data) |
| [france-bank-transactions-dashboard](./projects/france-bank-transactions-dashboard) | Bank-statement transaction category breakdown (anonymized data) |
| [luxembourg-rental-dashboard](./projects/luxembourg-rental-dashboard) | Luxembourg rental listing price/surface explorer |

Each app is self-contained (`app.py`, `data.py`, `requirements.txt`, bundled
data, tests) and independently deployable to Streamlit Community Cloud.

## Running an app locally

```bash
cd projects/<app-name>
pip install -r requirements.txt
streamlit run app.py
```
```

- [ ] **Step 2: Commit**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects
git add README.md
git commit -m "Update streamlit-projects README with links to all 6 dashboard apps"
```

---

## Final step: push everything

- [ ] **Push all commits to GitHub**

```bash
cd /Users/amine_jalili/Desktop/test/streamlit-projects
git push origin main
```

Expected: all 14 tasks' commits appear on `github.com/AJoo22/streamlit-projects`.
