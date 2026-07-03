import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_df():
    return pd.DataFrame({
        "Customer ID": [1, 2, 3, 4],
        "Age": [25, 30, 40, 22],
        "Gender": ["Female", "Male", "Female", "Male"],
        "Location": ["City A", "City B", "City A", "City B"],
        "Annual Income": [40000, 60000, 50000, 30000],
    })


def test_load_data(tmp_path):
    df = make_df()
    csv_path = tmp_path / "e.csv"
    df.to_csv(csv_path, index=False)
    loaded = d.load_data(str(csv_path))
    assert pd.api.types.is_numeric_dtype(loaded["Annual Income"])


def test_filter_data():
    df = make_df()
    filtered = d.filter_data(df, ["Female"], ["City A"])
    assert len(filtered) == 2
    assert (filtered["Gender"] == "Female").all()


def test_compute_kpis_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert kpis["customer_count"] == 0


def test_compute_kpis_nonempty():
    kpis = d.compute_kpis(make_df())
    assert kpis["customer_count"] == 4
    assert kpis["avg_income"] == 45000.0


def test_compute_kpis_counts_unique_customers_not_rows():
    # Duplicate rows for the same customer (e.g. repeat purchase snapshots)
    # must not inflate the customer_count KPI.
    df = pd.DataFrame({
        "Customer ID": [1, 2, 3, 4, 1],
        "Age": [25, 30, 40, 22, 26],
        "Gender": ["Female", "Male", "Female", "Male", "Female"],
        "Location": ["City A", "City B", "City A", "City B", "City A"],
        "Annual Income": [40000, 60000, 50000, 30000, 44000],
    })
    kpis = d.compute_kpis(df)
    assert len(df) == 5
    assert kpis["customer_count"] == 4
    assert kpis["avg_income"] == 44800.0


def test_compute_kpis_customer_count_matches_real_csv_unique_customers():
    data_path = Path(__file__).resolve().parents[1] / "data" / "E-commerce.csv"
    df = d.load_data(str(data_path))
    kpis = d.compute_kpis(df)
    assert len(df) == 50
    assert kpis["customer_count"] == 13
    assert kpis["customer_count"] != len(df)


def test_income_by_gender():
    result = d.income_by_gender(make_df())
    assert result["Female"] == 90000
    assert result["Male"] == 90000


def test_sorted_income():
    result = d.sorted_income(make_df())
    assert list(result) == [30000, 40000, 50000, 60000]


def test_kpi_narrative_empty():
    kpis = d.compute_kpis(make_df().iloc[0:0])
    assert d.kpi_narrative(kpis) == "No customers match the current filters."


def test_kpi_narrative_nonempty():
    kpis = d.compute_kpis(make_df())
    result = d.kpi_narrative(kpis)
    assert "4" in result
    assert "45,000" in result


def test_income_by_gender_insight():
    result = d.income_by_gender_insight(d.income_by_gender(make_df()))
    assert "%" in result
    assert "Female" in result or "Male" in result


def test_income_by_gender_insight_empty():
    empty = d.income_by_gender(make_df().iloc[0:0])
    assert d.income_by_gender_insight(empty) == "No income data available for the current selection."


def test_sorted_income_insight():
    result = d.sorted_income_insight(d.sorted_income(make_df()))
    assert "30,000" in result
    assert "60,000" in result
    assert "2.0x" in result


def test_sorted_income_insight_empty():
    result = d.sorted_income_insight(d.sorted_income(make_df().iloc[0:0]))
    assert result == "No income data available for the current selection."
