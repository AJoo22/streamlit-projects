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
