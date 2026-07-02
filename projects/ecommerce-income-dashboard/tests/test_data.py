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


def test_income_by_gender():
    result = d.income_by_gender(make_df())
    assert result["Female"] == 90000
    assert result["Male"] == 90000


def test_sorted_income():
    result = d.sorted_income(make_df())
    assert list(result) == [30000, 40000, 50000, 60000]
