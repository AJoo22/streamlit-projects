import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

CATEGORY_RULES = [
    ("Salaire", "Salary"),
    ("Employer Payroll", "Salary"),
    ("Pharmacy", "Health"),
    ("Grocery Market", "Groceries"),
    ("Telecom Provider", "Utilities"),
    ("Utility Provider", "Utilities"),
    ("Coffee Shop", "Dining"),
    ("Retail Store", "Shopping"),
    ("Electronics Store", "Shopping"),
    ("Online Shop", "Shopping"),
    ("Transport Ticket", "Transport"),
    ("Agency Deposit", "Deposit"),
    ("Contact", "Transfer"),
    ("Frais Tenue de compte", "Fees"),
    ("solde", "Balance"),
    ("Total", "Balance"),
]


def categorize(label):
    for keyword, category in CATEGORY_RULES:
        if keyword.lower() in str(label).lower():
            return category
    return "Other"


def _month_of(date_str):
    parts = str(date_str).split(".")
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    month_str = parts[1]
    if month_str == "1":
        return 10  # trailing zero dropped from "10" upstream in the source data (float round-trip artifact)
    return int(month_str)


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "filtered_data_fixed.csv")
    df = pd.read_csv(path, sep=";")
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    df["Débit"] = pd.to_numeric(df["Débit"], errors="coerce").fillna(0)
    df["Crédit"] = pd.to_numeric(df["Crédit"], errors="coerce").fillna(0)
    df["Category"] = df["Libellé des opérations"].apply(categorize)
    df["Month"] = df["Date opé."].apply(_month_of)
    df = df[df["Category"] != "Balance"]
    return df


def filter_data(df, categories, months):
    return df[df["Category"].isin(categories) & df["Month"].isin(months)]


def compute_kpis(df):
    if df.empty:
        return {"total_debit": 0.0, "total_credit": 0.0, "transaction_count": 0}
    return {
        "total_debit": float(df["Débit"].sum()),
        "total_credit": float(df["Crédit"].sum()),
        "transaction_count": int(len(df)),
    }


def category_breakdown(df):
    return df.groupby("Category")[["Débit", "Crédit"]].sum()


def monthly_credit_debit(df):
    return df.groupby("Month")[["Débit", "Crédit"]].sum().reset_index().sort_values("Month")


def largest_transactions(df, n=10):
    return (
        df.assign(Amount=df["Débit"] + df["Crédit"])
        .sort_values("Amount", ascending=False)
        .head(n)
    )


def kpi_narrative(kpis):
    if kpis["transaction_count"] == 0:
        return "No transactions match the current filters."
    net = kpis["total_credit"] - kpis["total_debit"]
    direction = "more money coming in than going out" if net >= 0 else "more money going out than coming in"
    return (
        f"Across **{kpis['transaction_count']}** transactions, there's {direction} — Crédit "
        f"totals **{kpis['total_credit']:,.2f}** against Débit of **{kpis['total_debit']:,.2f}**."
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


def monthly_trend_insight(monthly_df):
    if monthly_df.empty or len(monthly_df) < 2:
        return "Not enough months in the current selection to describe a trend."
    first, last = monthly_df.iloc[0], monthly_df.iloc[-1]
    debit_change = last["Débit"] - first["Débit"]
    direction = "grew" if debit_change >= 0 else "shrank"
    return (
        f"Month over month, spending (Débit) {direction} from **{first['Débit']:,.0f}** in "
        f"month {int(first['Month'])} to **{last['Débit']:,.0f}** in month {int(last['Month'])}."
    )


def largest_transactions_insight(largest_df):
    if largest_df.empty:
        return "No transactions to show for the current selection."
    top = largest_df.iloc[0]
    return (
        f"The single biggest transaction shown is **{top['Amount']:,.2f}** in the "
        f"**{top['Category']}** category — worth a look if it's unexpected."
    )
