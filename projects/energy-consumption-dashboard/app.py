# projects/energy-consumption-dashboard/app.py
import json

import streamlit as st
import plotly.express as px
import pandas as pd

import data as d

st.set_page_config(page_title="Energy Consumption Dashboard", page_icon="⚡", layout="wide")

# One fixed color per region/source so the same thing is always the same
# color across every chart on the page, instead of shifting with Plotly's
# default palette depending on which categories happen to be filtered in.
REGION_COLORS = {
    "Île-de-France": "#4C78A8", "Nouvelle-Aquitaine": "#F58518",
    "Auvergne-Rhône-Alpes": "#54A24B", "Bourgogne-Franche-Comté": "#E45756",
    "Bretagne": "#72B7B2", "Centre-Val de Loire": "#EECA3B",
    "Grand Est": "#B279A2", "Hauts-de-France": "#FF9DA6",
    "Normandie": "#9D755D", "Occitanie": "#BAB0AC",
    "Pays de la Loire": "#4C78A8", "Provence-Alpes-Côte d'Azur": "#F58518",
}
SOURCE_COLORS = {
    "Thermique": "#B279A2", "Nucléaire": "#E45756", "Eolien": "#54A24B",
    "Solaire": "#F2CF5B", "Hydraulique": "#4C78A8", "Pompage": "#9D755D",
    "Bioénergies": "#72B7B2",
}


@st.cache_resource
def get_geojson():
    with open(d.GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


st.title("⚡ France Energy Consumption & Production Dashboard")
st.caption(
    "Sample of the public RTE éCO2mix regional dataset (12 mainland regions, 2021–2023). "
    "Full dataset: https://www.rte-france.com/eco2mix"
)
st.markdown(
    "Descriptive analytics (regional and source-mix breakdowns), a feature-correlation "
    "analysis, a 6-model regression comparison, and a SARIMAX time-series forecast — end "
    "to end from raw éCO2mix records to predictive modeling."
)


@st.cache_data
def get_data():
    return d.load_data()


with st.spinner("Loading grid data..."):
    df = get_data()

regions = sorted(df["Région"].unique())
min_date, max_date = df["Date"].min().date(), df["Date"].max().date()

st.sidebar.header("Filters")
st.sidebar.caption("Narrow the data below — every chart and metric updates together.")
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
date_range = st.sidebar.slider(
    "Date range", min_value=min_date, max_value=max_date, value=(min_date, max_date)
)

filtered = d.filter_data(df, selected_regions, date_range[0], date_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
balance = kpis["total_production"] - kpis["total_consumption"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Consumption (MW)", f"{kpis['total_consumption']:,.0f}")
col2.metric(
    "Total Production (MW)", f"{kpis['total_production']:,.0f}",
    delta=f"{balance:+,.0f} vs consumption",
)
col3.metric("Avg Daily Consumption (MW)", f"{kpis['avg_daily_consumption']:,.0f}")
col4.metric("Dominant Source", kpis["dominant_source"])
st.markdown(d.kpi_narrative(kpis))

st.divider()

tab_overview, tab_trends, tab_predict, tab_data = st.tabs(
    ["📊 Overview", "📈 Trends & Correlations", "🔮 Predictions", "🗂️ Data"]
)

with tab_overview:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Consumption by Region")
        region_series = d.consumption_by_region(filtered)
        region_df = region_series.reset_index()
        region_df.columns = ["Région", "Consommation (MW)"]
        st.plotly_chart(
            px.bar(
                region_df, x="Région", y="Consommation (MW)", color="Région",
                color_discrete_map=REGION_COLORS,
            ),
            use_container_width=True,
        )
        st.markdown(d.region_insight(region_series))
    with col_b:
        st.subheader("Consumption by Region — Map")
        map_df = d.regional_map_data(filtered)
        if map_df.empty:
            st.info("No regional data available for the current selection.")
        else:
            fig = px.choropleth(
                map_df, geojson=get_geojson(), locations="Code INSEE région",
                featureidkey="properties.code", color="Consommation (MW)",
                hover_name="Région", color_continuous_scale="Reds",
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(d.map_insight(map_df))

    st.subheader("Production Mix")
    mix_series = d.production_mix(filtered)
    st.plotly_chart(
        px.pie(
            values=mix_series.values, names=mix_series.index,
            color=mix_series.index, color_discrete_map=SOURCE_COLORS,
        ),
        use_container_width=True,
    )
    st.markdown(d.mix_insight(mix_series))

with tab_trends:
    st.subheader("Production & Consumption Over Time")
    trend_df = d.production_over_time(filtered)
    fig = px.line(trend_df, x="Date", y=["Production (MW)", "Consommation (MW)"])
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(d.trend_insight(trend_df))

    st.subheader("Correlation Heatmap")
    st.caption("How closely each production source and usage rate tracks consumption.")
    corr_df = d.correlation_matrix(filtered)
    st.plotly_chart(
        px.imshow(corr_df, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1),
        use_container_width=True,
    )
    st.markdown(d.correlation_insight(corr_df))

with tab_predict:
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

    st.subheader("Model Comparison")
    st.caption(
        "Tests 6 machine learning models side by side to see which one predicts consumption "
        "most accurately from the production mix alone. Trains on the full selection, so it "
        "can take a moment on a large date range."
    )
    if st.button("Run model comparison"):
        with st.spinner("Training 6 models..."):
            comparison_df = d.compare_models(filtered)
        if comparison_df is None:
            st.info("Not enough data in the current filter selection to compare models.")
        else:
            st.plotly_chart(
                px.bar(comparison_df, x="Model", y="RMSE", color="R2", color_continuous_scale="Blues_r"),
                use_container_width=True,
            )
            st.dataframe(comparison_df, use_container_width=True)
            st.markdown(d.model_comparison_insight(comparison_df))

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

with tab_data:
    st.subheader("Filtered Data")
    st.caption(f"{len(filtered):,} rows match the current filters.")
    st.dataframe(filtered, use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name="energy_consumption_filtered.csv",
        mime="text/csv",
    )
