# Energy Consumption Dashboard

Interactive Streamlit dashboard for exploring French national grid (RTE éCO2mix)
regional energy consumption and production data: consumption by region, energy
production mix, trends over time, a linear regression model predicting
consumption from the production mix, and an on-demand SARIMAX forecast.

Bundled data is a trimmed sample (3 regions, 2021+) of the full public
[RTE éCO2mix](https://www.rte-france.com/eco2mix) dataset, sized to fit
comfortably in git and Streamlit Community Cloud's free tier.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest tests/ -v
```
