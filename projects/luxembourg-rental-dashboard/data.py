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


def kpi_narrative(kpis):
    if kpis["listing_count"] == 0:
        return "No listings match the current filters."
    return (
        f"In plain terms: among **{kpis['listing_count']}** listings, the typical (median) "
        f"rent is **€{kpis['median_price']:,.0f}**, working out to about "
        f"**€{kpis['avg_price_per_sqm']:,.1f} per m²** on average."
    )


def price_distribution_insight(df):
    if df.empty:
        return "No price data available for the current selection."
    return (
        f"Rents shown here range from **€{df['Price'].min():,.0f}** to "
        f"**€{df['Price'].max():,.0f}**, with half the listings priced below "
        f"**€{df['Price'].median():,.0f}**."
    )


def surface_distribution_insight(df):
    if df.empty:
        return "No surface data available for the current selection."
    return (
        f"Apartment sizes range from **{df['Surface'].min():,.0f} m²** to "
        f"**{df['Surface'].max():,.0f} m²**, with half the listings smaller than "
        f"**{df['Surface'].median():,.0f} m²**."
    )


def price_vs_surface_insight(df):
    if len(df) < 2:
        return "Not enough listings to describe the price-vs-surface relationship."
    corr = df["Price"].corr(df["Surface"])
    if pd.isna(corr):
        return "Not enough variation in this selection to describe the price-vs-surface relationship."
    strength = "strongly" if abs(corr) >= 0.7 else "moderately" if abs(corr) >= 0.4 else "only weakly"
    return (
        f"Bigger apartments are {strength} linked to higher rent here (correlation of "
        f"{corr:.2f}) — as a rule of thumb, size explains {'most' if abs(corr) >= 0.7 else 'some' if abs(corr) >= 0.4 else 'little'} "
        f"of why one listing costs more than another."
    )


def location_insight(location_counts):
    if location_counts.empty:
        return "No location data available for the current selection."
    total = location_counts.sum()
    top = location_counts.index[0]
    share = location_counts.iloc[0] / total * 100
    return (
        f"**{top}** has the most listings shown here, at {share:.0f}% of the total — "
        f"more listings usually means more choice, but also more competition among renters."
    )
