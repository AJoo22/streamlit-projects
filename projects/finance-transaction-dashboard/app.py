import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Finance Transaction Dashboard", layout="wide")
st.title("Personal Finance Transaction Dashboard")
st.caption("All amounts and merchant descriptions are anonymized/randomized — not real transactions.")


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

st.subheader("Monthly Crédit vs Débit")
monthly = d.monthly_credit_debit(filtered)
st.plotly_chart(px.line(monthly, x="YearMonth", y=["Débit", "Crédit"]), use_container_width=True)

st.subheader("Category Breakdown")
breakdown = d.category_breakdown(filtered).reset_index()
st.plotly_chart(px.bar(breakdown, x="Category", y=["Débit", "Crédit"], barmode="group"), use_container_width=True)

st.subheader("Filtered Transactions")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="finance_transactions_filtered.csv",
    mime="text/csv",
)
