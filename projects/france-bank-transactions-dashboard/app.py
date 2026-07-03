# projects/france-bank-transactions-dashboard/app.py
import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Bank Transactions Dashboard", layout="wide")
st.title("Bank Statement Transactions Dashboard")
st.caption("All amounts and merchant descriptions are anonymized/randomized — not real transactions.")
st.markdown(
    "In plain terms: this page shows what you spend money on, whether that spending is "
    "trending up or down month to month, and which single transactions stand out most."
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

categories = sorted(df["Category"].dropna().unique())
months = sorted(df["Month"].dropna().unique())

st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
selected_months = st.sidebar.multiselect("Month", months, default=months)

filtered = d.filter_data(df, selected_categories, selected_months)

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Total Crédit", f"{kpis['total_credit']:,.2f}")
col2.metric("Total Débit", f"{kpis['total_debit']:,.2f}")
col3.metric("Transactions", kpis["transaction_count"])
st.markdown(d.kpi_narrative(kpis))

st.subheader("Category Breakdown")
breakdown = d.category_breakdown(filtered)
st.plotly_chart(px.bar(breakdown.reset_index(), x="Category", y=["Débit", "Crédit"], barmode="group"), use_container_width=True)
st.markdown(d.category_breakdown_insight(breakdown))

st.subheader("Monthly Crédit vs Débit")
monthly = d.monthly_credit_debit(filtered)
st.plotly_chart(px.line(monthly, x="Month", y=["Débit", "Crédit"]), use_container_width=True)
st.markdown(d.monthly_trend_insight(monthly))

st.subheader("Largest Transactions")
largest = d.largest_transactions(filtered, n=10)
st.dataframe(largest)
st.markdown(d.largest_transactions_insight(largest))

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="bank_transactions_filtered.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Why this matters")
st.markdown(
    "- **Budgeting:** the monthly trend shows whether spending is climbing before it "
    "becomes a surprise at the end of the month.\n"
    "- **Category awareness:** knowing which category eats the biggest share of Débit "
    "makes it obvious where a budget cut would actually help.\n"
    "- **Catching outliers:** the largest-transactions table flags the few payments worth "
    "double-checking."
)
