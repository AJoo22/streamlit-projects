# Bank Transactions Dashboard

Interactive Streamlit dashboard for bank-statement-derived transaction data:
category breakdown (categorized by merchant-description keyword matching),
largest transactions, filterable by category and month.

All amounts and merchant descriptions are anonymized/randomized — not real
transaction data.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest tests/ -v
```
