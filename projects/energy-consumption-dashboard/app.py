# projects/energy-consumption-dashboard/app.py
import streamlit as st
import plotly.express as px
import pandas as pd

import data as d

st.set_page_config(page_title="Energy Consumption Dashboard", layout="wide")
st.title("France Energy Consumption & Production Dashboard")
st.caption(
    "Sample of the public RTE éCO2mix regional dataset (3 regions, 2021+). "
    "Full dataset: https://www.rte-france.com/eco2mix"
)
st.markdown(
    "This dashboard turns raw hourly grid records into a story about regional demand, "
    "the generation mix behind it, and where consumption is headed next — useful for "
    "spotting supply gaps, tracking renewable adoption, and planning ahead of demand growth."
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

regions = sorted(df["Région"].unique())
min_date, max_date = df["Date"].min().date(), df["Date"].max().date()

st.sidebar.header("Filters")
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
date_range = st.sidebar.slider(
    "Date range", min_value=min_date, max_value=max_date, value=(min_date, max_date)
)

filtered = d.filter_data(df, selected_regions, date_range[0], date_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Consumption (MW)", f"{kpis['total_consumption']:,.0f}")
col2.metric("Total Production (MW)", f"{kpis['total_production']:,.0f}")
col3.metric("Avg Daily Consumption (MW)", f"{kpis['avg_daily_consumption']:,.0f}")
col4.metric("Dominant Source", kpis["dominant_source"])
st.markdown(d.kpi_narrative(kpis))

st.subheader("Consumption by Region")
region_series = d.consumption_by_region(filtered)
st.plotly_chart(px.bar(region_series, labels={"value": "Consommation (MW)", "index": "Région"}), use_container_width=True)
st.markdown(d.region_insight(region_series))

st.subheader("Production Mix")
mix_series = d.production_mix(filtered)
st.plotly_chart(px.pie(values=mix_series.values, names=mix_series.index), use_container_width=True)
st.markdown(d.mix_insight(mix_series))

st.subheader("Production & Consumption Over Time")
trend_df = d.production_over_time(filtered)
fig = px.line(trend_df, x="Date", y=["Production (MW)", "Consommation (MW)"])
st.plotly_chart(fig, use_container_width=True)
st.markdown(d.trend_insight(trend_df))

st.subheader("Linear Regression: Predicting Consumption")
reg_result = d.fit_regression(filtered)
if reg_result is None:
    st.info("Not enough data in the current filter selection to fit a regression model.")
else:
    reg_col1, reg_col2 = st.columns(2)
    reg_col1.metric("RMSE", f"{reg_result['rmse']:,.1f}")
    reg_col2.metric("R²", f"{reg_result['r2']:.3f}")
    scatter_df = pd.DataFrame({"Actual": reg_result["y_test"], "Predicted": reg_result["y_pred"]})
    st.plotly_chart(px.scatter(scatter_df, x="Actual", y="Predicted"), use_container_width=True)
    st.markdown(d.regression_insight(reg_result))

st.subheader("SARIMAX Forecast")
forecast_region = st.selectbox("Region to forecast", selected_regions)
if st.button("Run forecast"):
    with st.spinner("Fitting SARIMAX model..."):
        forecast_result = d.fit_forecast(filtered, forecast_region)
    if forecast_result is None:
        st.info("Not enough monthly history for this region/date range to forecast (need 24+ months).")
    else:
        hist = forecast_result["history"].rename(columns={"Consommation (MW)": "Value"})
        hist["Series"] = "Historical"
        fut = forecast_result["forecast"].rename(columns={"Forecast (MW)": "Value"})
        fut["Series"] = "Forecast"
        combined = pd.concat([hist, fut])
        st.plotly_chart(px.line(combined, x="Date", y="Value", color="Series"), use_container_width=True)
        st.markdown(d.forecast_insight(forecast_result))

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="energy_consumption_filtered.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Why this matters")
st.markdown(
    "- **Grid planning:** regional consumption gaps flag where transmission capacity "
    "may need to grow.\n"
    "- **Renewable transition:** the production-mix share tracks how fast wind, solar, "
    "hydro, and bioenergy are displacing thermal and nuclear generation.\n"
    "- **Demand forecasting:** the regression and SARIMAX models translate historical "
    "patterns into concrete numbers utilities and policymakers can plan capacity around."
)
