# Finance Transaction Dashboard

Interactive Streamlit dashboard for categorized bank-transaction data: monthly
credit/debit trends and category breakdowns, filterable by category and month.

All monetary amounts and merchant descriptions are anonymized/randomized —
not real transaction data.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest tests/ -v
```
