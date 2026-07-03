import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data as d


def make_csv(tmp_path):
    content = (
        "Date opé.;Date valeur;Libellé des opérations;Débit;Crédit;\n"
        "9.07;9.07;Carte X1234 Grocery Market B;10.0;;\n"
        "9.07;9.07;Virement Employer Payroll Salaire;;2000.0;\n"
        "10.08;10.08;Carte X1234 Pharmacy D;20.0;;\n"
    )
    path = tmp_path / "f.csv"
    path.write_text(content)
    return str(path)


def test_categorize():
    assert d.categorize("Carte X1234 Grocery Market B") == "Groceries"
    assert d.categorize("Virement Employer Payroll Salaire") == "Salary"
    assert d.categorize("Something Unknown") == "Other"


def test_load_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    assert "Category" in df.columns
    assert "Month" in df.columns
    assert set(df["Month"]) == {7, 8}


def test_filter_data(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    filtered = d.filter_data(df, ["Groceries"], [7])
    assert len(filtered) == 1


def test_compute_kpis(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    kpis = d.compute_kpis(df)
    assert kpis["total_credit"] == 2000.0
    assert kpis["total_debit"] == 30.0
    assert kpis["transaction_count"] == 3


def test_category_breakdown(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.category_breakdown(df)
    assert result.loc["Salary", "Crédit"] == 2000.0


def test_largest_transactions(tmp_path):
    df = d.load_data(make_csv(tmp_path))
    result = d.largest_transactions(df, n=1)
    assert len(result) == 1
    assert result.iloc[0]["Category"] == "Salary"


def test_month_of_bare_one_is_october():
    # Upstream source data drops the trailing zero from "10" via a float
    # round-trip (float("31.10") == 31.1), so a bare ".1" month token means
    # October, never January in this file's convention.
    assert d._month_of("31.1") == 10


def test_month_of_zero_padded_one_is_january():
    assert d._month_of("5.01") == 1
