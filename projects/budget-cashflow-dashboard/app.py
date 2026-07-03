import streamlit as st
import plotly.express as px

import data as d

st.set_page_config(page_title="Budget & Cash Flow Dashboard", layout="wide")
st.title("Personal Budget & Cash Flow Dashboard")
st.caption("All monetary values are anonymized/randomized — not real financial data.")
st.markdown(
    "In plain terms: this page tracks money coming in vs going out, which expenses take "
    "the biggest bite, and whether savings are growing over time."
)


@st.cache_data
def get_data():
    return d.load_data()


df = get_data()

all_categories = d.cashflow_categories(df) + d.expense_categories(df) + [d.NET_WORTH_CATEGORY]
months = sorted(df["Month"].unique())

st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect("Category", all_categories, default=all_categories)
month_range = st.sidebar.select_slider(
    "Month range",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda m: m.strftime("%Y-%m"),
)

filtered = d.filter_data(df, selected_categories, month_range[0], month_range[1])

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = d.compute_kpis(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Total Cash Flow", f"{kpis['total_cashflow']:,.2f}")
col2.metric("Total Expenses", f"{kpis['total_expenses']:,.2f}")
col3.metric("Avg Monthly Cash Flow", f"{kpis['avg_monthly_cashflow']:,.2f}")
st.markdown(d.kpi_narrative(kpis))

st.subheader("Cash Flow by Category Over Time")
cashflow_trend = d.cashflow_by_category_over_time(filtered)
if cashflow_trend.empty:
    st.info("No cash flow categories selected.")
else:
    st.plotly_chart(px.line(cashflow_trend, x="Month", y="Amount", color="Category"), use_container_width=True)
    st.markdown(d.cashflow_trend_insight(cashflow_trend))

st.subheader("Expense Breakdown")
expenses = d.expense_breakdown(filtered)
if expenses.empty:
    st.info("No expense categories selected.")
else:
    st.plotly_chart(
        px.bar(expenses.reset_index(), x="Category", y="Amount"), use_container_width=True
    )
    st.markdown(d.expense_breakdown_insight(expenses))

st.subheader("Net Worth Trend (Safe Keep)")
net_worth = d.net_worth_trend(filtered)
if net_worth.empty:
    st.info("Net worth category not in the current filter selection.")
else:
    st.plotly_chart(px.line(net_worth, x="Month", y="Amount"), use_container_width=True)
    st.markdown(d.net_worth_insight(net_worth))

st.subheader("Filtered Data")
st.dataframe(filtered)
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="budget_cashflow_filtered.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Why this matters")
st.markdown(
    "- **Staying ahead:** tracking cash flow vs expenses monthly catches a shortfall "
    "before it becomes a problem.\n"
    "- **Cutting costs:** the expense breakdown shows exactly which category to target "
    "first for the biggest savings.\n"
    "- **Long-term progress:** the net worth trend is the simplest check that savings "
    "are actually moving in the right direction."
)
