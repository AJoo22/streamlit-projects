import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "luxembourg_properties.csv")
    df = pd.read_csv(path)
    is_range = df["Price"].astype(str).str.contains("à", na=False)
    df.loc[is_range, "Price"] = None
    df["Price"] = (
        df["Price"].astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=True)
        .str.replace(r"[^0-9.]", "", regex=True)
        .str.strip()
    )
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Surface"] = df["Surface"].astype(str).str.extract(r"(\d+)", expand=False)
    df["Surface"] = pd.to_numeric(df["Surface"], errors="coerce")
    return df.dropna(subset=["Price", "Surface"]).reset_index(drop=True)


def filter_data(df, locations, price_range, surface_range):
    mask = (
        df["Location"].isin(locations)
        & df["Price"].between(price_range[0], price_range[1])
        & df["Surface"].between(surface_range[0], surface_range[1])
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"avg_price": 0.0, "median_price": 0.0, "listing_count": 0, "avg_price_per_sqm": 0.0}
    price_per_sqm = (df["Price"] / df["Surface"]).replace([float("inf")], pd.NA).dropna()
    return {
        "avg_price": float(df["Price"].mean()),
        "median_price": float(df["Price"].median()),
        "listing_count": int(len(df)),
        "avg_price_per_sqm": float(price_per_sqm.mean()) if not price_per_sqm.empty else 0.0,
    }


def listings_by_location(df):
    return df["Location"].value_counts()
