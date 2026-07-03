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
