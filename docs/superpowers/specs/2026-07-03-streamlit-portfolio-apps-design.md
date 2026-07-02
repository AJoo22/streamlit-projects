# Design: Convert data-analysis-portfolio projects into Streamlit apps

## Goal

Turn 6 of the 7 projects in `data-analysis-portfolio` into interactive Streamlit
apps, living in `streamlit-projects/projects/`, so the portfolio has runnable,
deployable dashboards instead of static scripts/notebooks.

`image-webp-converter` is excluded — it's a batch utility, not an analysis
dashboard.

## Scope

Six apps, one per source project:

1. `energy-consumption-analysis` → `projects/energy-consumption-dashboard/`
2. `ecommerce-income-analysis` → `projects/ecommerce-income-dashboard/`
3. `finance-transaction-cleaning` → `projects/finance-transaction-dashboard/`
4. `budget-cashflow-tracker` → `projects/budget-cashflow-dashboard/`
5. `france-bank-transactions` → `projects/france-bank-transactions-dashboard/`
6. `luxembourg-rental-scraper` → `projects/luxembourg-rental-dashboard/`

Source data for each app is copied from the already-anonymized CSVs in
`data-analysis-portfolio` (no new anonymization work needed — that's already
done).

## Common app template

Every app folder contains:

```
projects/<app-name>/
  app.py
  requirements.txt
  data/<bundled anonymized csv(s)>
  README.md
  .github/workflows/streamlit.yml   # CI smoke test, same pattern as energie-app
```

Every `app.py` follows the same internal structure:

- `st.set_page_config(...)` + title/intro text
- Sidebar: filters relevant to that dataset (date range, category/region/location
  dropdowns — see per-app table below)
- Top row: `st.columns` of KPI metric tiles (`st.metric`) summarizing the
  filtered data
- One or more interactive Plotly charts (`st.plotly_chart`) driven by the
  sidebar filters — replacing the original static matplotlib charts with the
  same analytical content
- A `st.dataframe` of the filtered rows
- A `st.download_button` to export the filtered view as CSV
- Data loaded via a `@st.cache_data`-decorated loader function

## Per-app functionality

| App | Filters | Views |
|---|---|---|
| energy-consumption-dashboard | region, date range | consumption by region (bar+pie), energy production mix, production trend over time, regression scatter (predicted vs actual, RMSE/R² as metrics) |
| ecommerce-income-dashboard | gender, city | income by gender, income distribution scatter, KPIs: avg/median income, customer count |
| finance-transaction-dashboard | category, month | categorized transaction table, monthly credit/debit trend, category breakdown |
| budget-cashflow-dashboard | month range, category | cash flow by category, expense breakdown, net-worth trend |
| france-bank-transactions-dashboard | category, month | credit/debit trend, category breakdown, largest-transactions table |
| luxembourg-rental-dashboard | location, price range, surface range | price distribution, surface distribution, price-vs-surface scatter, listings by location |

### energy-consumption-dashboard: forecasting exception

The SARIMAX forecast is compute-heavy (fits a seasonal ARIMA model). It runs
behind an explicit "Run forecast" button rather than on every page load/filter
change, so the default page stays fast. Regression (linear model) is cheap
enough to run inline with filters.

### energy-consumption-dashboard: data exception

The full RTE éCO2mix dataset is ~305MB — too large for git or Streamlit
Community Cloud's free tier. This app instead bundles a trimmed sample: 2-3
regions, most recent ~2 years of data, clearly labeled in the README and in
the app UI as a sample of the full public dataset (with a link to the full
source).

## Charting library

Plotly (`plotly.express` / `plotly.graph_objects`), not matplotlib — needed
for hover/zoom/pan interactivity paired with the sidebar filters. Original
matplotlib scripts in `data-analysis-portfolio` are left untouched; this is a
new, separate set of apps.

## Out of scope

- Actually deploying each app to share.streamlit.io — no public API for this,
  requires a manual click-through by the user for each app after this work
  lands in GitHub.
- Changes to the original `data-analysis-portfolio` static scripts/notebooks.
- `image-webp-converter`.

## Testing approach

For each app: run `streamlit run app.py` locally, exercise every filter and
button once, confirm charts render and update, confirm no exceptions in the
terminal. No automated test suite — these are portfolio demo apps; the
GitHub Actions workflow does a headless smoke-test boot (matching the
existing `energie-app` CI pattern) to catch import/syntax errors on push.
