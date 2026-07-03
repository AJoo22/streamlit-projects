import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="E-commerce Income Dashboard", layout="wide")
st.title("E-commerce Customer Income Dashboard")
st.caption("Synthetic e-commerce customer dataset — not real customer data.")
st.markdown(
    "In plain terms: this page shows who your customers are and how much they earn, so you "
    "can spot which groups matter most and how unequal income is across your customer base."
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

genders = sorted(df["Gender"].dropna().unique())
locations = sorted(df["Location"].dropna().unique())

st.sidebar.header("Filters")
selected_genders = st.sidebar.multiselect("Gender", genders, default=genders)
selected_locations = st.sidebar.multiselect("Location", locations, default=locations)

filtered = d.filter_data(df, selected_genders, selected_locations)

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Avg Annual Income", f"${kpis['avg_income']:,.0f}")
col2.metric("Median Annual Income", f"${kpis['median_income']:,.0f}")
col3.metric("Customers", kpis["customer_count"])
st.markdown(d.kpi_narrative(kpis))

st.subheader("Total Annual Income by Gender")
income_series = d.income_by_gender(filtered)
st.plotly_chart(px.bar(income_series, orientation="h"), use_container_width=True)
st.markdown(d.income_by_gender_insight(income_series))

st.subheader("Annual Income Distribution (sorted)")
sorted_series = d.sorted_income(filtered)
st.plotly_chart(px.scatter(x=sorted_series.index, y=sorted_series.values, labels={"x": "Index", "y": "Annual Income"}), use_container_width=True)
st.markdown(d.sorted_income_insight(sorted_series))

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="ecommerce_filtered.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Why this matters")
st.markdown(
    "- **Targeting:** knowing which groups earn (and spend) the most helps prioritize "
    "marketing budget where it pays off.\n"
    "- **Fairness check:** a wide gap between the lowest and highest earners can flag "
    "whether your customer base — or your pricing — skews toward one income bracket.\n"
    "- **Simple, no black box:** every number here is a plain sum, average, or sort — easy "
    "to explain to anyone, technical or not."
)
