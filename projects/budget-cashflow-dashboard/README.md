# Budget & Cash Flow Dashboard

Interactive Streamlit dashboard for monthly cash flow by income category,
expense breakdown, and a net-worth ("safe keep" savings) trend, filterable by
category and month range.

Built from `fichiers.csv` (the tidy category-by-month cash flow export). All
monetary values are anonymized/randomized — not real financial data.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest tests/ -v
```
