import os

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor
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
RENEWABLE_SOURCES = ["Eolien", "Solaire", "Hydraulique", "Bioénergies"]
# Approximate regional centroids (lat, lon), used only to place bubbles on the map.
REGION_COORDINATES = {
    "Île-de-France": (48.7, 2.5),
    "Nouvelle-Aquitaine": (45.2, 0.3),
    "Auvergne-Rhône-Alpes": (45.3, 4.0),
}
MODEL_FACTORIES = {
    "Linear Regression": lambda: LinearRegression(),
    "Ridge Regression": lambda: Ridge(alpha=1.0),
    "Lasso Regression": lambda: Lasso(alpha=0.1),
    "Decision Tree": lambda: DecisionTreeRegressor(random_state=0, max_depth=5),
    "Random Forest": lambda: RandomForestRegressor(
        random_state=0, n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2
    ),
    "Gradient Boosting": lambda: GradientBoostingRegressor(random_state=0, n_estimators=200),
}


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


def regional_map_data(df):
    region_series = consumption_by_region(df)
    rows = [
        {"Région": region, "Consommation (MW)": total, "lat": lat, "lon": lon}
        for region, total in region_series.items()
        for lat, lon in [REGION_COORDINATES[region]]
        if region in REGION_COORDINATES
    ]
    return pd.DataFrame(rows, columns=["Région", "Consommation (MW)", "lat", "lon"])


def map_insight(map_df):
    if map_df.empty:
        return "No regional data to plot on the map."
    top = map_df.loc[map_df["Consommation (MW)"].idxmax()]
    return (
        f"Bubble size and color both track consumption — **{top['Région']}** is the biggest "
        f"circle on the map, meaning it consumes the most electricity of the selected regions."
    )


def production_mix(df):
    mix = df[PRODUCTION_COLUMNS].sum()
    mix.index = [c.replace(" (MW)", "") for c in mix.index]
    return mix


def production_over_time(df):
    daily = df.groupby(df["Date"].dt.date)[["Production (MW)", "Consommation (MW)"]].sum()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.reset_index().rename(columns={"index": "Date"})
    return daily


def correlation_matrix(df):
    feature_cols = [c for c in PRODUCTION_COLUMNS + TCO_COLUMNS if c in df.columns]
    cols = feature_cols + ["Consommation (MW)"]
    return df[cols].corr()


def correlation_insight(corr_df):
    if corr_df.empty or "Consommation (MW)" not in corr_df.columns:
        return "Not enough data to describe correlations."
    corr_with_consumption = corr_df["Consommation (MW)"].drop("Consommation (MW)")
    if corr_with_consumption.empty:
        return "Not enough data to describe correlations."
    top = corr_with_consumption.abs().idxmax()
    value = corr_with_consumption[top]
    strength = "strongly" if abs(value) >= 0.7 else "moderately" if abs(value) >= 0.4 else "weakly"
    relation = "positively" if value >= 0 else "negatively"
    return (
        f"**{top}** is the strongest correlate of consumption ({relation} correlated, "
        f"r = {value:.2f}) — a {strength} linear relationship."
    )


def compare_models(df):
    feature_cols = [c for c in PRODUCTION_COLUMNS if c in df.columns]
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
    rows = []
    for name, factory in MODEL_FACTORIES.items():
        model = factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = float(r2_score(y_test, y_pred))
        rows.append({"Model": name, "RMSE": rmse, "R2": r2})
    return pd.DataFrame(rows).sort_values("RMSE").reset_index(drop=True)


def model_comparison_insight(comparison_df):
    if comparison_df is None or comparison_df.empty:
        return "Not enough data to compare models."
    best = comparison_df.iloc[0]
    worst = comparison_df.iloc[-1]
    improvement = (worst["RMSE"] - best["RMSE"]) / worst["RMSE"] * 100 if worst["RMSE"] else 0.0
    return (
        f"**{best['Model']}** is the most accurate here, with a typical error of "
        f"{best['RMSE']:,.0f} MW (R²={best['R2']:.2f}) — {improvement:.0f}% less error than "
        f"the weakest model, **{worst['Model']}**."
    )


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


def kpi_narrative(kpis):
    if kpis["total_consumption"] == 0:
        return "No data available for the current selection."
    balance = kpis["total_production"] - kpis["total_consumption"]
    balance_pct = balance / kpis["total_consumption"] * 100
    direction = "surplus" if balance >= 0 else "deficit"
    return (
        f"Selected regions produced {abs(balance_pct):.1f}% "
        f"{'more' if balance >= 0 else 'less'} energy than they consumed over this period "
        f"(a {direction}), with **{kpis['dominant_source']}** the largest single source of production."
    )


def region_insight(region_series):
    if region_series.empty:
        return "No regional data available for the current selection."
    total = region_series.sum()
    top_region = region_series.index[0]
    top_share = region_series.iloc[0] / total * 100
    if len(region_series) > 1:
        gap = (region_series.iloc[0] - region_series.iloc[1]) / region_series.iloc[1] * 100
        return (
            f"**{top_region}** consumes the most at {top_share:.0f}% of the total across "
            f"selected regions, {gap:.0f}% ahead of the next-highest region."
        )
    return f"**{top_region}** is the only region selected, consuming {region_series.iloc[0]:,.0f} MW."


def mix_insight(mix_series):
    total = mix_series.sum()
    if mix_series.empty or total == 0:
        return "No production data available for the current selection."
    dominant = mix_series.idxmax()
    dominant_share = mix_series[dominant] / total * 100
    renewable_share = mix_series[mix_series.index.isin(RENEWABLE_SOURCES)].sum() / total * 100
    return (
        f"**{dominant}** supplies {dominant_share:.0f}% of production. Renewables "
        f"(wind, solar, hydro, bioenergy combined) account for {renewable_share:.0f}% of the mix."
    )


def trend_insight(trend_df):
    if trend_df.empty or len(trend_df) < 2:
        return "Not enough data to describe a trend."
    first_cons = trend_df["Consommation (MW)"].iloc[0]
    last_cons = trend_df["Consommation (MW)"].iloc[-1]
    change_pct = (last_cons - first_cons) / first_cons * 100 if first_cons else 0.0
    direction = "risen" if change_pct >= 0 else "fallen"
    avg_gap = (trend_df["Production (MW)"] - trend_df["Consommation (MW)"]).mean()
    gap_word = "ahead of" if avg_gap >= 0 else "behind"
    return (
        f"Daily consumption has {direction} {abs(change_pct):.0f}% from the start to the end "
        f"of the selected period, with production running {gap_word} consumption by "
        f"{abs(avg_gap):,.0f} MW on average per day."
    )


def regression_insight(reg_result):
    r2_pct = reg_result["r2"] * 100
    quality = "strong" if reg_result["r2"] >= 0.7 else "moderate" if reg_result["r2"] >= 0.4 else "weak"
    return (
        f"The production mix explains {r2_pct:.0f}% of the variation in consumption "
        f"({quality} fit), with a typical prediction error of {reg_result['rmse']:,.0f} MW."
    )


def forecast_insight(forecast_result):
    hist_avg = forecast_result["history"]["Consommation (MW)"].tail(12).mean()
    forecast_avg = forecast_result["forecast"]["Forecast (MW)"].mean()
    change_pct = (forecast_avg - hist_avg) / hist_avg * 100 if hist_avg else 0.0
    direction = "higher" if change_pct >= 0 else "lower"
    return (
        f"The model projects consumption averaging {abs(change_pct):.0f}% {direction} over "
        f"the next 12 months compared to the trailing 12-month average."
    )


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
