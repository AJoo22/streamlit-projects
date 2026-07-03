import os

import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data(path=None):
    if path is None:
        path = os.path.join(_DATA_DIR, "E-commerce.csv")
    df = pd.read_csv(path)
    df["Annual Income"] = pd.to_numeric(df["Annual Income"], errors="coerce")
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    return df


def filter_data(df, genders, locations):
    mask = df["Gender"].isin(genders) & df["Location"].isin(locations)
    return df[mask]


def compute_kpis(df):
    if df.empty:
        return {"avg_income": 0.0, "median_income": 0.0, "customer_count": 0}
    return {
        "avg_income": float(df["Annual Income"].mean()),
        "median_income": float(df["Annual Income"].median()),
        "customer_count": int(df["Customer ID"].nunique()),
    }


def income_by_gender(df):
    return df.groupby("Gender")["Annual Income"].sum().sort_values(ascending=False)


def sorted_income(df):
    return df["Annual Income"].dropna().sort_values().reset_index(drop=True)


def kpi_narrative(kpis):
    if kpis["customer_count"] == 0:
        return "No customers match the current filters."
    return (
        f"Across **{kpis['customer_count']}** customers, the average person earns "
        f"**${kpis['avg_income']:,.0f}** a year. Half of customers earn more than "
        f"**${kpis['median_income']:,.0f}** and half earn less — that middle number "
        f"(the median) is often a better sense of the 'typical' customer than the average, "
        f"since a few very high earners can pull the average up."
    )


def income_by_gender_insight(income_series):
    total = income_series.sum()
    if income_series.empty or total == 0:
        return "No income data available for the current selection."
    top = income_series.index[0]
    share = income_series.iloc[0] / total * 100
    return (
        f"**{top}** customers bring in {share:.0f}% of all the income shown here — that's "
        f"simply because this group spends the most combined, not necessarily because any "
        f"one person earns more."
    )


def sorted_income_insight(sorted_series):
    if sorted_series.empty:
        return "No income data available for the current selection."
    lowest = sorted_series.iloc[0]
    highest = sorted_series.iloc[-1]
    gap_multiple = highest / lowest if lowest else float("inf")
    return (
        f"Reading left to right, each dot is one customer sorted from lowest to highest "
        f"income — from **${lowest:,.0f}** up to **${highest:,.0f}**. The highest earner "
        f"makes about **{gap_multiple:.1f}x** what the lowest earner makes, which shows how "
        f"spread out incomes are in this group."
    )
