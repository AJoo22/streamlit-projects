import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "FInance_cleaned.csv")
    df = pd.read_csv(path, sep=";")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Débit"] = pd.to_numeric(df["Débit"], errors="coerce").fillna(0)
    df["Crédit"] = pd.to_numeric(df["Crédit"], errors="coerce").fillna(0)
    df = df.rename(columns={"Category Improved": "Category"})
    return df


def filter_data(df, categories, start_month, end_month):
    mask = (
        df["Category"].isin(categories)
        & (df["YearMonth"] >= start_month)
        & (df["YearMonth"] <= end_month)
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"total_debit": 0.0, "total_credit": 0.0, "net": 0.0, "transaction_count": 0}
    total_debit = float(df["Débit"].sum())
    total_credit = float(df["Crédit"].sum())
    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net": total_credit - total_debit,
        "transaction_count": int(len(df)),
    }


def monthly_credit_debit(df):
    return df.groupby("YearMonth")[["Débit", "Crédit"]].sum().reset_index().sort_values("YearMonth")


def category_breakdown(df):
    return df.groupby("Category")[["Débit", "Crédit"]].sum()
