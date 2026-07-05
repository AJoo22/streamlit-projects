import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_csv(tmp_path):
    content = (
        "Price,Location,Surface\n"
        "1 200 €,Luxembourg-Centre,45 m²\n"
        "900 €,Luxembourg-Neudorf,29 m²\n"
        "not-a-price,Luxembourg-Gare,invalid\n"
    )
    path = tmp_path / "l.csv"
    path.write_text(content)
    return str(path)


def test_load_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert len(df) == 2
    assert df["Price"].tolist() == [1200.0, 900.0]
    assert df["Surface"].tolist() == [45.0, 29.0]


def test_filter_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    filtered = d.filter_data(df, ["Luxembourg-Centre"], (0, 2000), (0, 100))
    assert len(filtered) == 1


def test_compute_kpis_empty():
    kpis = d.compute_kpis(pd.DataFrame(columns=["Price", "Surface", "Location"]))
    assert kpis["listing_count"] == 0


def test_compute_kpis_nonempty(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    assert kpis["listing_count"] == 2
    assert kpis["avg_price"] == 1050.0


def test_listings_by_location(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.listings_by_location(df)
    assert result["Luxembourg-Centre"] == 1


def make_range_price_csv(tmp_path):
    content = (
        "Price,Location,Surface\n"
        "1 200 €,Luxembourg-Centre,45 m²\n"
        "900 €,Luxembourg-Neudorf,29 m²\n"
        "De 970 € à 1 070 720 €,Differdange,50 m²\n"
    )
    path = tmp_path / "range.csv"
    path.write_text(content)
    return str(path)


def test_load_data_excludes_price_range_rows(tmp_path):
    df = d.load_data(make_range_price_csv(tmp_path))
    assert "Differdange" not in df["Location"].tolist()
    assert len(df) == 2
    assert df["Price"].max() < 10000


def test_kpi_narrative_empty():
    kpis = d.compute_kpis(pd.DataFrame(columns=["Price", "Surface", "Location"]))
    assert d.kpi_narrative(kpis) == "No listings match the current filters."


def test_kpi_narrative_nonempty(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    result = d.kpi_narrative(kpis)
    assert "2" in result
    assert "1,050" in result


def test_price_distribution_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.price_distribution_insight(df)
    assert "900" in result
    assert "1,200" in result


def test_price_distribution_insight_empty():
    empty = pd.DataFrame(columns=["Price"])
    assert d.price_distribution_insight(empty) == "No price data available for the current selection."


def test_surface_distribution_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.surface_distribution_insight(df)
    assert "29" in result
    assert "45" in result


def test_surface_distribution_insight_empty():
    empty = pd.DataFrame(columns=["Surface"])
    assert d.surface_distribution_insight(empty) == "No surface data available for the current selection."


def test_price_vs_surface_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.price_vs_surface_insight(df)
    assert "correlation of" in result


def test_price_vs_surface_insight_insufficient_data(tmp_path):
    df = d.load_data(make_csv(tmp_path)).iloc[:1]
    assert d.price_vs_surface_insight(df) == "Not enough listings to describe the price-vs-surface relationship."


def test_location_insight(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.location_insight(d.listings_by_location(df))
    assert "Luxembourg-Centre" in result or "Luxembourg-Neudorf" in result
    assert "%" in result


def test_location_insight_empty():
    assert d.location_insight(pd.Series(dtype=int)) == "No location data available for the current selection."


def make_value_df():
    rows = []
    for i in range(12):
        rows.append({"Price": 500.0 + i, "Surface": 50.0, "Location": "CheapTown"})
    for i in range(15):
        rows.append({"Price": 3000.0 + i, "Surface": 50.0, "Location": "PriceyTown"})
    for i in range(5):
        rows.append({"Price": 100000.0, "Surface": 10.0, "Location": "TinyTown"})
    return pd.DataFrame(rows)


def test_value_by_location_excludes_small_samples():
    df = make_value_df()
    result = d.value_by_location(df, min_listings=10)
    assert set(result["Location"]) == {"CheapTown", "PriceyTown"}


def test_value_by_location_sorted_ascending():
    df = make_value_df()
    result = d.value_by_location(df, min_listings=10)
    assert result.iloc[0]["Location"] == "CheapTown"
    assert result.iloc[-1]["Location"] == "PriceyTown"


def test_value_by_location_empty():
    result = d.value_by_location(pd.DataFrame(columns=["Price", "Surface", "Location"]))
    assert result.empty


def test_value_insight():
    df = make_value_df()
    value_df = d.value_by_location(df, min_listings=10)
    result = d.value_insight(value_df)
    assert "CheapTown" in result
    assert "PriceyTown" in result
    assert "x" in result


def test_value_insight_no_qualifying_locations():
    empty = pd.DataFrame(columns=["Location", "listings", "avg_price_per_sqm", "avg_price"])
    result = d.value_insight(empty)
    assert "at least" in result
