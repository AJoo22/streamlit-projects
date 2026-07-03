# Luxembourg Rental Dashboard

Interactive Streamlit dashboard for Luxembourg rental listing data: price and
surface distributions, price-vs-surface scatter, and listing counts by
location, filterable by location, price range, and surface range.

Data is public listing information scraped from athome.lu — no owner or
tenant personal data is included.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest tests/ -v
```
