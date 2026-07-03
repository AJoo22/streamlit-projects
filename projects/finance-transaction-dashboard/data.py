import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "FInance_cleaned.csv")
    df = pd.read_csv(path, sep=";")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Débit"] = pd.to_numeric(df["Débit"], errors="coerce").fillna(0)
    df["Crédit"] = pd.to_numeric(df["Crédit"], errors="coerce").fillna(0)
    df = df.rename(columns={"Category Improved": "Category"})
    return df


def filter_data(df, categories, start_month, end_month):
    mask = (
        df["Category"].isin(categories)
        & (df["YearMonth"] >= start_month)
        & (df["YearMonth"] <= end_month)
    )
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"total_debit": 0.0, "total_credit": 0.0, "net": 0.0, "transaction_count": 0}
    total_debit = float(df["Débit"].sum())
    total_credit = float(df["Crédit"].sum())
    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net": total_credit - total_debit,
        "transaction_count": int(len(df)),
    }


def monthly_credit_debit(df):
    return df.groupby("YearMonth")[["Débit", "Crédit"]].sum().reset_index().sort_values("YearMonth")


def category_breakdown(df):
    return df.groupby("Category")[["Débit", "Crédit"]].sum()


def category_month_trend(df):
    grouped = df.groupby(["Category", "YearMonth"])[["Débit", "Crédit"]].sum().reset_index()
    melted = grouped.melt(
        id_vars=["Category", "YearMonth"], value_vars=["Débit", "Crédit"],
        var_name="Type", value_name="Amount",
    )
    return melted.sort_values("YearMonth")


def amount_distribution(df):
    melted = df.melt(
        id_vars=["Category"], value_vars=["Débit", "Crédit"],
        var_name="Type", value_name="Amount",
    )
    return melted[melted["Amount"] > 0]


def kpi_narrative(kpis):
    if kpis["transaction_count"] == 0:
        return "No transactions match the current filters."
    direction = "more money coming in than going out" if kpis["net"] >= 0 else "more money going out than coming in"
    return (
        f"Across **{kpis['transaction_count']}** transactions, there's {direction} — a net "
        f"of **{kpis['net']:,.2f}** (Crédit {kpis['total_credit']:,.2f} minus Débit "
        f"{kpis['total_debit']:,.2f})."
    )


def monthly_trend_insight(monthly_df):
    if monthly_df.empty or len(monthly_df) < 2:
        return "Not enough months in the current selection to describe a trend."
    first, last = monthly_df.iloc[0], monthly_df.iloc[-1]
    debit_change = last["Débit"] - first["Débit"]
    direction = "grew" if debit_change >= 0 else "shrank"
    return (
        f"Monthly spending (Débit) {direction} from **{first['Débit']:,.0f}** in "
        f"{first['YearMonth']} to **{last['Débit']:,.0f}** in {last['YearMonth']}."
    )


def category_breakdown_insight(breakdown_df):
    if breakdown_df.empty:
        return "No category data available for the current selection."
    total_debit = breakdown_df["Débit"].sum()
    if total_debit == 0:
        return "No spending data available for the current selection."
    top_category = breakdown_df["Débit"].idxmax()
    top_value = breakdown_df["Débit"].max()
    share = top_value / total_debit * 100
    return (
        f"**{top_category}** is the single biggest spending category, making up "
        f"{share:.0f}% of total Débit shown here."
    )


def category_month_trend_insight(trend_df):
    if trend_df.empty:
        return "No category trend data for the current selection."
    debit = trend_df[trend_df["Type"] == "Débit"]
    if debit.empty:
        return "No spending trend data for the current selection."
    pivot = debit.pivot_table(index="Category", columns="YearMonth", values="Amount", aggfunc="sum").fillna(0)
    if pivot.shape[1] < 2:
        return "Not enough months in the current selection to describe a trend."
    first_col, last_col = pivot.columns[0], pivot.columns[-1]
    change = pivot[last_col] - pivot[first_col]
    top_category = change.idxmax()
    top_change = change[top_category]
    direction = "increased" if top_change >= 0 else "decreased"
    return (
        f"**{top_category}** spending {direction} the most from the first to the last month "
        f"shown, changing by **{abs(top_change):,.0f}**. Watching category trends like this "
        f"over time helps spot new habits before they add up."
    )


def amount_distribution_insight(dist_df):
    if dist_df.empty:
        return "No transaction amounts to show for the current selection."
    median_amount = dist_df["Amount"].median()
    max_amount = dist_df["Amount"].max()
    return (
        f"Most individual transactions are small — the typical (median) transaction is "
        f"**{median_amount:,.0f}**, while the biggest single transaction shown is "
        f"**{max_amount:,.0f}**. A histogram like this shows whether spending comes from "
        f"many small purchases or a few large ones."
    )
