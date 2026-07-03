import csv
import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FRENCH_MONTHS = {
    "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6,
    "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12,
}

CASHFLOW_PREFIX = "CASHFLOW_"
EXPENSE_CATEGORIES = [
    "Affitto", "Cibo Fuori", "Spesa", "Regali", "Investimento", "Coiffeur",
    "Divertimento", "Abbonamenti", "Luce", "Treno", "Vestiti",
]
NET_WORTH_CATEGORY = "SAFE KEEP"


def _parse_month_column(col):
    year_str, month_str = col.split("-")
    return pd.Timestamp(year=int(year_str), month=FRENCH_MONTHS[month_str], day=1)


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "fichiers.csv")
    # The bundled CSV export is ragged: some rows are missing a trailing
    # value (short row) and some have extra trailing values beyond the
    # header's month columns (long row, with no reliable way to know what
    # months those extras represent). pandas.read_csv's fixed-width C
    # parser raises on both cases, so we parse row-by-row instead: pad
    # short rows with empty strings and truncate long rows to the header
    # length.
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        month_cols = header[1:]
        n_months = len(month_cols)

        records = []
        for row in reader:
            if not row:
                continue
            category = row[0]
            values = row[1:]
            if len(values) < n_months:
                values = values + [""] * (n_months - len(values))
            elif len(values) > n_months:
                values = values[:n_months]
            records.append([category] + values)

    df = pd.DataFrame(records, columns=["Category"] + month_cols)
    long_df = df.melt(id_vars="Category", value_vars=month_cols, var_name="MonthLabel", value_name="Amount")
    long_df["Amount"] = pd.to_numeric(long_df["Amount"], errors="coerce")
    long_df = long_df.dropna(subset=["Amount"])
    long_df["Month"] = long_df["MonthLabel"].apply(_parse_month_column)
    return long_df


def filter_data(df, categories, start_month, end_month):
    mask = (
        df["Category"].isin(categories)
        & (df["Month"] >= pd.Timestamp(start_month))
        & (df["Month"] <= pd.Timestamp(end_month))
    )
    return df[mask]


def cashflow_categories(df):
    return sorted(c for c in df["Category"].unique() if c.startswith(CASHFLOW_PREFIX))


def expense_categories(df):
    return sorted(c for c in df["Category"].unique() if c in EXPENSE_CATEGORIES)


def compute_kpis(df):
    cashflow_df = df[df["Category"].str.startswith(CASHFLOW_PREFIX)]
    expense_df = df[df["Category"].isin(EXPENSE_CATEGORIES)]
    if df.empty:
        return {"total_cashflow": 0.0, "total_expenses": 0.0, "avg_monthly_cashflow": 0.0}
    total_cashflow = float(cashflow_df["Amount"].sum())
    total_expenses = float(expense_df["Amount"].sum())
    avg_monthly = float(cashflow_df.groupby("Month")["Amount"].sum().mean()) if not cashflow_df.empty else 0.0
    return {
        "total_cashflow": total_cashflow,
        "total_expenses": total_expenses,
        "avg_monthly_cashflow": avg_monthly,
    }


def cashflow_by_category_over_time(df):
    cashflow_df = df[df["Category"].str.startswith(CASHFLOW_PREFIX)]
    return cashflow_df.groupby(["Month", "Category"])["Amount"].sum().reset_index()


def expense_breakdown(df):
    expense_df = df[df["Category"].isin(EXPENSE_CATEGORIES)]
    return expense_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)


def net_worth_trend(df):
    net_worth_df = df[df["Category"] == NET_WORTH_CATEGORY]
    return net_worth_df.groupby("Month")["Amount"].sum().reset_index().sort_values("Month")


def kpi_narrative(kpis):
    if kpis["total_cashflow"] == 0 and kpis["total_expenses"] == 0:
        return "No data available for the current selection."
    net = kpis["total_cashflow"] - kpis["total_expenses"]
    direction = "more coming in than going out" if net >= 0 else "more going out than coming in"
    return (
        f"In plain terms: over this period there's {direction} — cash flow of "
        f"**{kpis['total_cashflow']:,.2f}** against expenses of **{kpis['total_expenses']:,.2f}**, "
        f"averaging **{kpis['avg_monthly_cashflow']:,.2f}** per month."
    )


def cashflow_trend_insight(cashflow_trend_df):
    if cashflow_trend_df.empty:
        return "No cash flow categories selected."
    totals = cashflow_trend_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    top = totals.index[0]
    return (
        f"**{top}** contributes the most to cash flow over the selected months — the line "
        f"for that category should sit above the others most of the time."
    )


def expense_breakdown_insight(expenses):
    if expenses.empty or expenses.sum() == 0:
        return "No expense categories selected."
    total = expenses.sum()
    top = expenses.index[0]
    share = expenses.iloc[0] / total * 100
    return (
        f"**{top}** is the single biggest expense, making up {share:.0f}% of total spending "
        f"shown here — the first place to look if you want to cut costs."
    )


def net_worth_insight(net_worth_df):
    if net_worth_df.empty or len(net_worth_df) < 2:
        return "Not enough months in the current selection to describe a trend."
    first = net_worth_df.iloc[0]["Amount"]
    last = net_worth_df.iloc[-1]["Amount"]
    change = last - first
    direction = "grown" if change >= 0 else "shrunk"
    return (
        f"Net worth (Safe Keep) has {direction} by **{abs(change):,.2f}** from the start to "
        f"the end of the selected months — a simple way to check if savings are moving in "
        f"the right direction."
    )
