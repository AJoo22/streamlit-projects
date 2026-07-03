import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.tsa.statespace.sarimax import SARIMAX

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

PRODUCTION_COLUMNS = [
    "Thermique (MW)", "Nucléaire (MW)", "Eolien (MW)", "Solaire (MW)",
    "Hydraulique (MW)", "Pompage (MW)", "Bioénergies (MW)",
]
TCO_COLUMNS = [
    "TCO Thermique (%)", "TCO Nucléaire (%)", "TCO Eolien (%)",
    "TCO Hydraulique (%)", "TCO Solaire (%)", "TCO Bioénergies (%)",
]


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "eco2mix_sample.csv")
    df = pd.read_csv(path, sep=";")
    for col in PRODUCTION_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Consommation (MW)"] = pd.to_numeric(df["Consommation (MW)"], errors="coerce").fillna(0)
    for col in TCO_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Production (MW)"] = df[PRODUCTION_COLUMNS].sum(axis=1)
    return df


def filter_data(df, regions, start_date, end_date):
    mask = (
        df["Région"].isin(regions)
        & (df["Date"] >= pd.Timestamp(start_date))
        & (df["Date"] <= pd.Timestamp(end_date))
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {
            "total_consumption": 0.0,
            "total_production": 0.0,
            "avg_daily_consumption": 0.0,
            "dominant_source": "N/A",
        }
    mix = df[PRODUCTION_COLUMNS].sum()
    return {
        "total_consumption": float(df["Consommation (MW)"].sum()),
        "total_production": float(df["Production (MW)"].sum()) if "Production (MW)" in df.columns else float(mix.sum()),
        "avg_daily_consumption": float(df.groupby(df["Date"].dt.date)["Consommation (MW)"].sum().mean()),
        "dominant_source": mix.idxmax().replace(" (MW)", ""),
    }


def consumption_by_region(df):
    return df.groupby("Région")["Consommation (MW)"].sum().sort_values(ascending=False)


def production_mix(df):
    mix = df[PRODUCTION_COLUMNS].sum()
    mix.index = [c.replace(" (MW)", "") for c in mix.index]
    return mix


def production_over_time(df):
    daily = df.groupby(df["Date"].dt.date)[["Production (MW)", "Consommation (MW)"]].sum()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.reset_index().rename(columns={"index": "Date"})
    return daily


def fit_regression(df):
    feature_cols = [c for c in PRODUCTION_COLUMNS + TCO_COLUMNS if c in df.columns]
    data = df.dropna(subset=feature_cols + ["Consommation (MW)"])
    if len(data) < 10:
        return None
    X = data[feature_cols]
    y = data["Consommation (MW)"]
    split = max(int(len(data) * 0.8), 1)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    if len(X_test) == 0:
        X_test, y_test = X_train, y_train
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))
    return {"y_test": y_test.values, "y_pred": y_pred, "rmse": rmse, "r2": r2}


def fit_forecast(df, region, periods=12):
    region_df = (
        df[df["Région"] == region]
        .groupby(df["Date"].dt.to_period("M"))["Consommation (MW)"]
        .sum()
    )
    if len(region_df) < 24:
        return None
    region_df.index = region_df.index.to_timestamp()
    model = SARIMAX(
        region_df,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    results = model.fit(disp=False)
    forecast = results.get_forecast(steps=periods)
    forecast_index = pd.date_range(start=region_df.index[-1], periods=periods + 1, freq="MS")[1:]
    forecast_df = pd.DataFrame({"Date": forecast_index, "Forecast (MW)": forecast.predicted_mean.values})
    history_df = region_df.reset_index()
    history_df.columns = ["Date", "Consommation (MW)"]
    return {"history": history_df, "forecast": forecast_df}
