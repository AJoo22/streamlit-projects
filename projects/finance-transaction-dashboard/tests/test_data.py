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


def test_category_month_trend():
    df = make_df().rename(columns={"Category Improved": "Category"})
    result = d.category_month_trend(df)
    assert set(result["Type"]) == {"Débit", "Crédit"}
    assert set(result["Category"]) == {"Salary", "Other"}


def test_amount_distribution_excludes_zero_amounts():
    df = make_df().rename(columns={"Category Improved": "Category"})
    result = d.amount_distribution(df)
    assert (result["Amount"] > 0).all()
    assert len(result) == 3


def test_kpi_narrative_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert d.kpi_narrative(kpis) == "No transactions match the current filters."


def test_kpi_narrative_nonempty():
    df = make_df().rename(columns={"Category Improved": "Category"})
    kpis = d.compute_kpis(df)
    result = d.kpi_narrative(kpis)
    assert "3" in result
    assert "more money coming in than going out" in result


def test_monthly_trend_insight():
    df = make_df().rename(columns={"Category Improved": "Category"})
    monthly = d.monthly_credit_debit(df)
    result = d.monthly_trend_insight(monthly)
    assert "grew" in result or "shrank" in result


def test_monthly_trend_insight_insufficient_data():
    monthly = d.monthly_credit_debit(make_df().iloc[0:0])
    assert d.monthly_trend_insight(monthly) == "Not enough months in the current selection to describe a trend."


def test_category_breakdown_insight():
    df = make_df().rename(columns={"Category Improved": "Category"})
    breakdown = d.category_breakdown(df)
    result = d.category_breakdown_insight(breakdown)
    assert "Other" in result
    assert "%" in result


def test_category_month_trend_insight():
    df = make_df().rename(columns={"Category Improved": "Category"})
    trend_df = d.category_month_trend(df)
    result = d.category_month_trend_insight(trend_df)
    assert "spending" in result
    assert "increased" in result or "decreased" in result


def test_amount_distribution_insight():
    df = make_df().rename(columns={"Category Improved": "Category"})
    dist_df = d.amount_distribution(df)
    result = d.amount_distribution_insight(dist_df)
    assert "median" in result
    assert "2,100" in result


def test_amount_distribution_insight_empty():
    empty = pd.DataFrame({"Amount": []})
    assert d.amount_distribution_insight(empty) == "No transaction amounts to show for the current selection."
