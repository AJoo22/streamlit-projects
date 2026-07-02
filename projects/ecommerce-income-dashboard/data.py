import pandas as pd


def load_data(path="data/E-commerce.csv"):
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
        "customer_count": int(len(df)),
    }


def income_by_gender(df):
    return df.groupby("Gender")["Annual Income"].sum().sort_values(ascending=False)


def sorted_income(df):
    return df["Annual Income"].dropna().sort_values().reset_index(drop=True)
