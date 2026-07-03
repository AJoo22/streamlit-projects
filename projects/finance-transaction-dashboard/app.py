import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Finance Transaction Dashboard", layout="wide")
st.title("Personal Finance Transaction Dashboard")
st.caption("All amounts and merchant descriptions are anonymized/randomized — not real transactions.")
st.markdown(
    "In plain terms: this page shows where money came from, where it went, and whether "
    "spending in each category is climbing or settling down over time."
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

categories = sorted(df["Category"].dropna().unique())
months = sorted(df["YearMonth"].dropna().unique())

st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
month_range = st.sidebar.select_slider("Month range", options=months, value=(months[0], months[-1]))

filtered = d.filter_data(df, selected_categories, month_range[0], month_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Crédit", f"{kpis['total_credit']:,.2f}")
col2.metric("Total Débit", f"{kpis['total_debit']:,.2f}")
col3.metric("Net", f"{kpis['net']:,.2f}")
col4.metric("Transactions", kpis["transaction_count"])
st.markdown(d.kpi_narrative(kpis))

st.subheader("Monthly Crédit vs Débit")
monthly = d.monthly_credit_debit(filtered)
st.plotly_chart(px.line(monthly, x="YearMonth", y=["Débit", "Crédit"]), use_container_width=True)
st.markdown(d.monthly_trend_insight(monthly))

st.subheader("Category Breakdown")
breakdown = d.category_breakdown(filtered)
st.plotly_chart(px.bar(breakdown.reset_index(), x="Category", y=["Débit", "Crédit"], barmode="group"), use_container_width=True)
st.markdown(d.category_breakdown_insight(breakdown))

st.subheader("Category Spending Over Time")
st.caption("Same categories as above, but split out month by month so you can see which ones are trending up or down.")
category_trend = d.category_month_trend(filtered)
st.plotly_chart(
    px.line(category_trend, x="YearMonth", y="Amount", color="Category", facet_col="Type"),
    use_container_width=True,
)
st.markdown(d.category_month_trend_insight(category_trend))

st.subheader("Transaction Amount Distribution")
st.caption("How big is a typical transaction? This groups every individual transaction by size.")
dist_df = d.amount_distribution(filtered)
st.plotly_chart(
    px.histogram(dist_df, x="Amount", color="Category", facet_col="Type", nbins=20, barmode="overlay", opacity=0.7),
    use_container_width=True,
)
st.markdown(d.amount_distribution_insight(dist_df))

st.subheader("Filtered Transactions")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="finance_transactions_filtered.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Why this matters")
st.markdown(
    "- **Budgeting:** seeing which category is growing month over month helps catch "
    "creeping expenses before they become a habit.\n"
    "- **Cash flow:** the Crédit-vs-Débit trend shows whether more money is coming in "
    "than going out, and when that balance shifts.\n"
    "- **Spotting outliers:** the transaction-size histogram flags whether spending is "
    "many small purchases or a few large ones — useful for catching one-off surprises."
)
