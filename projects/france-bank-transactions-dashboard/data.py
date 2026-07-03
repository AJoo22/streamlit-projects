import pandas as pd

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


def load_data(path="data/filtered_data_fixed.csv"):
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


def largest_transactions(df, n=10):
    return (
        df.assign(Amount=df["Débit"] + df["Crédit"])
        .sort_values("Amount", ascending=False)
        .head(n)
    )
