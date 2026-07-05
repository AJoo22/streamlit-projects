# projects/luxembourg-rental-dashboard/app.py
import streamlit as st
import plotly.express as px
import pandas as pd

import data as d

st.set_page_config(page_title="Luxembourg Rental Dashboard", layout="wide")
st.title("Luxembourg Rental Listings Dashboard")
st.caption(
    "Public rental listing data scraped from athome.lu — no owner/tenant personal data. "
    "Covers the full advertised rental market, not a price-limited segment."
)
st.markdown(
    "Price and surface distributions, a price-vs-surface correlation, listing "
    "concentration by location, and — the practical question — **where a rent budget "
    "actually stretches furthest**, ranked by average €/m² across the market."
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

locations = sorted(df["Location"].dropna().unique())
price_min, price_max = float(df["Price"].min()), float(df["Price"].max())
surface_min, surface_max = float(df["Surface"].min()), float(df["Surface"].max())

st.sidebar.header("Filters")
selected_locations = st.sidebar.multiselect("Location", locations, default=locations)
price_range = st.sidebar.slider("Price (€)", price_min, price_max, (price_min, price_max))
surface_range = st.sidebar.slider("Surface (m²)", surface_min, surface_max, (surface_min, surface_max))

filtered = d.filter_data(df, selected_locations, price_range, surface_range)

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Price", f"€{kpis['avg_price']:,.0f}")
col2.metric("Median Price", f"€{kpis['median_price']:,.0f}")
col3.metric("Listings", kpis["listing_count"])
col4.metric("Avg €/m²", f"€{kpis['avg_price_per_sqm']:,.1f}")
st.markdown(d.kpi_narrative(kpis))

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Price Distribution")
    st.plotly_chart(px.histogram(filtered, x="Price", nbins=20), use_container_width=True)
    st.markdown(d.price_distribution_insight(filtered))
with col_b:
    st.subheader("Surface Distribution")
    st.plotly_chart(px.histogram(filtered, x="Surface", nbins=20), use_container_width=True)
    st.markdown(d.surface_distribution_insight(filtered))

st.subheader("Price vs Surface")
st.plotly_chart(px.scatter(filtered, x="Surface", y="Price", color="Location"), use_container_width=True)
st.markdown(d.price_vs_surface_insight(filtered))

st.subheader("Listings by Location")
location_counts = d.listings_by_location(filtered)
st.plotly_chart(px.bar(location_counts), use_container_width=True)
st.markdown(d.location_insight(location_counts))

st.divider()
st.subheader("Where Does Your Rent Go Furthest?")
st.caption(
    f"Ranks locations by average €/m², limited to those with at least "
    f"{d.MIN_LISTINGS_FOR_VALUE_RANKING} listings so a handful of outlier ads can't skew it."
)
value_df = d.value_by_location(filtered)
if value_df.empty:
    st.info(d.value_insight(value_df))
else:
    extremes = pd.concat([value_df.head(10), value_df.tail(10)]).drop_duplicates(subset="Location")
    st.plotly_chart(
        px.bar(
            extremes, x="Location", y="avg_price_per_sqm",
            labels={"avg_price_per_sqm": "Avg €/m²"},
            color="avg_price_per_sqm", color_continuous_scale="RdYlGn_r",
        ),
        use_container_width=True,
    )
    st.markdown(d.value_insight(value_df))

st.subheader("Filtered Listings")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="luxembourg_listings_filtered.csv",
    mime="text/csv",
)

