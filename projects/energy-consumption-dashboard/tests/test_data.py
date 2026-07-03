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


def test_regional_map_data():
    df = make_df()
    map_df = d.regional_map_data(df)
    assert set(map_df["Région"]) == {"Île-de-France", "Nouvelle-Aquitaine"}
    assert {"lat", "lon", "Consommation (MW)"}.issubset(map_df.columns)


def test_regional_map_data_empty():
    map_df = d.regional_map_data(make_df().iloc[0:0])
    assert map_df.empty


def test_map_insight():
    df = make_df()
    result = d.map_insight(d.regional_map_data(df))
    assert "Île-de-France" in result or "Nouvelle-Aquitaine" in result


def test_map_insight_empty():
    assert d.map_insight(d.regional_map_data(make_df().iloc[0:0])) == "No regional data to plot on the map."


def test_compare_models_enough_data():
    df = make_df()
    result = d.compare_models(df)
    assert result is not None
    assert set(result["Model"]) == set(d.MODEL_FACTORIES.keys())
    assert (result["RMSE"] >= 0).all()
    assert result["RMSE"].is_monotonic_increasing


def test_compare_models_insufficient_data():
    df = make_df().iloc[:5]
    assert d.compare_models(df) is None


def test_model_comparison_insight():
    df = make_df()
    comparison_df = d.compare_models(df)
    result = d.model_comparison_insight(comparison_df)
    assert "most accurate" in result


def test_model_comparison_insight_none():
    assert d.model_comparison_insight(None) == "Not enough data to compare models."


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


def test_kpi_narrative_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert d.kpi_narrative(kpis) == "No data available for the current selection."


def test_kpi_narrative_nonempty():
    df = make_df()
    df["Production (MW)"] = df[[
        "Thermique (MW)", "Nucléaire (MW)", "Eolien (MW)", "Solaire (MW)",
        "Hydraulique (MW)", "Pompage (MW)", "Bioénergies (MW)",
    ]].sum(axis=1)
    kpis = d.compute_kpis(df)
    narrative = d.kpi_narrative(kpis)
    assert "Nucléaire" in narrative
    assert "surplus" in narrative or "deficit" in narrative


def test_region_insight_multiple_regions():
    df = make_df()
    result = d.region_insight(d.consumption_by_region(df))
    assert "Nouvelle-Aquitaine" in result or "Île-de-France" in result
    assert "%" in result


def test_region_insight_empty():
    empty = d.consumption_by_region(make_df().iloc[0:0])
    assert "No regional data" in d.region_insight(empty)


def test_mix_insight():
    df = make_df()
    result = d.mix_insight(d.production_mix(df))
    assert "Nucléaire" in result
    assert "Renewables" in result


def test_mix_insight_empty():
    empty = d.production_mix(make_df().iloc[0:0])
    assert "No production data" in d.mix_insight(empty)


def test_trend_insight():
    df = make_df()
    df["Production (MW)"] = df[[
        "Thermique (MW)", "Nucléaire (MW)", "Eolien (MW)", "Solaire (MW)",
        "Hydraulique (MW)", "Pompage (MW)", "Bioénergies (MW)",
    ]].sum(axis=1)
    trend_df = d.production_over_time(df)
    result = d.trend_insight(trend_df)
    assert "risen" in result or "fallen" in result


def test_trend_insight_insufficient_data():
    df = make_df().iloc[0:0].copy()
    df["Production (MW)"] = df[[
        "Thermique (MW)", "Nucléaire (MW)", "Eolien (MW)", "Solaire (MW)",
        "Hydraulique (MW)", "Pompage (MW)", "Bioénergies (MW)",
    ]].sum(axis=1)
    trend_df = d.production_over_time(df)
    assert d.trend_insight(trend_df) == "Not enough data to describe a trend."


def test_correlation_matrix():
    df = make_df()
    corr = d.correlation_matrix(df)
    assert "Consommation (MW)" in corr.columns
    assert "Nucléaire (MW)" in corr.index


def test_correlation_insight():
    df = make_df()
    corr = d.correlation_matrix(df)
    result = d.correlation_insight(corr)
    assert "correlation of" in result
    assert "strongly" in result or "moderately" in result or "weakly" in result


def test_correlation_insight_empty():
    empty_corr = pd.DataFrame()
    assert d.correlation_insight(empty_corr) == "Not enough data to describe correlations."


def test_regression_insight():
    df = make_df()
    reg_result = d.fit_regression(df)
    result = d.regression_insight(reg_result)
    assert "%" in result
    assert "MW" in result


def test_forecast_insight():
    forecast_result = {
        "history": pd.DataFrame({
            "Date": pd.date_range("2020-01-01", periods=12, freq="MS"),
            "Consommation (MW)": [1000] * 12,
        }),
        "forecast": pd.DataFrame({
            "Date": pd.date_range("2021-01-01", periods=12, freq="MS"),
            "Forecast (MW)": [1100] * 12,
        }),
    }
    result = d.forecast_insight(forecast_result)
    assert "higher" in result
    assert "10%" in result
