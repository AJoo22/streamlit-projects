import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_csv(tmp_path):
    content = (
        "Category,2023-Janvier,2023-Février\n"
        "CASHFLOW_LAVORO,1000.00,1200.00\n"
        "Affitto,200.00,200.00\n"
        "Cibo Fuori,50.00,60.00\n"
        "SAFE KEEP,500.00,700.00\n"
    )
    path = tmp_path / "fichiers.csv"
    path.write_text(content)
    return str(path)


def test_load_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert "Month" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Month"])
    assert df["Amount"].notna().all()


def test_filter_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    filtered = d.filter_data(df, ["CASHFLOW_LAVORO"], "2023-01-01", "2023-01-31")
    assert len(filtered) == 1
    assert filtered.iloc[0]["Amount"] == 1000.00


def test_cashflow_categories(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert d.cashflow_categories(df) == ["CASHFLOW_LAVORO"]


def test_expense_categories(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert set(d.expense_categories(df)) == {"Affitto", "Cibo Fuori"}


def test_compute_kpis(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    assert kpis["total_cashflow"] == 2200.00
    assert kpis["total_expenses"] == 510.00


def test_cashflow_by_category_over_time(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.cashflow_by_category_over_time(df)
    assert set(result["Category"]) == {"CASHFLOW_LAVORO"}


def test_expense_breakdown(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.expense_breakdown(df)
    assert result["Affitto"] == 400.00


def test_net_worth_trend(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.net_worth_trend(df)
    assert len(result) == 2
