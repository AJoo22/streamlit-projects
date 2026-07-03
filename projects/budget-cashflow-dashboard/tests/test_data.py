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


def test_load_data_real_bundled_file():
    # Regression test: the real shipped fichiers.csv has ragged rows
    # (some short by one field, some with extra trailing fields beyond
    # the header's month columns). pandas.read_csv's strict fixed-width
    # parser used to raise ParserError on this file. load_data must
    # tolerate that raggedness and still produce usable data.
    repo_root = Path(__file__).resolve().parents[1]
    df = d.load_data(str(repo_root / "data" / "fichiers.csv"))
    assert not df.empty
    assert list(df.columns) == ["Category", "MonthLabel", "Amount", "Month"]
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


def test_kpi_narrative_empty():
    kpis = {"total_cashflow": 0.0, "total_expenses": 0.0, "avg_monthly_cashflow": 0.0}
    assert d.kpi_narrative(kpis) == "No data available for the current selection."


def test_kpi_narrative_nonempty(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    result = d.kpi_narrative(kpis)
    assert "more coming in than going out" in result
    assert "2,200.00" in result


def test_cashflow_trend_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    trend = d.cashflow_by_category_over_time(df)
    result = d.cashflow_trend_insight(trend)
    assert "CASHFLOW_LAVORO" in result


def test_cashflow_trend_insight_empty():
    assert d.cashflow_trend_insight(pd.DataFrame()) == "No cash flow categories selected."


def test_expense_breakdown_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    expenses = d.expense_breakdown(df)
    result = d.expense_breakdown_insight(expenses)
    assert "Affitto" in result
    assert "78%" in result


def test_expense_breakdown_insight_empty():
    assert d.expense_breakdown_insight(pd.Series(dtype=float)) == "No expense categories selected."


def test_net_worth_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    net_worth = d.net_worth_trend(df)
    result = d.net_worth_insight(net_worth)
    assert "grown" in result
    assert "200.00" in result


def test_net_worth_insight_insufficient_data():
    net_worth = pd.DataFrame({"Month": [pd.Timestamp("2023-01-01")], "Amount": [500.0]})
    assert d.net_worth_insight(net_worth) == "Not enough months in the current selection to describe a trend."
