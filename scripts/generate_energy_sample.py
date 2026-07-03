# /Users/amine_jalili/Desktop/test/streamlit-projects/scripts/generate_energy_sample.py
import pandas as pd

SRC = "/Users/amine_jalili/Archive/data_analysis_Portfolio-source-2026-07-03/jeuxDeDonéesDataScientest/eco2mix-regional-cons-def copie.csv"
DST = "/Users/amine_jalili/Desktop/test/streamlit-projects/projects/energy-consumption-dashboard/data/eco2mix_sample.csv"

COLUMNS = [
    "Région", "Date", "Consommation (MW)", "Thermique (MW)", "Nucléaire (MW)",
    "Eolien (MW)", "Solaire (MW)", "Hydraulique (MW)", "Pompage (MW)",
    "Bioénergies (MW)", "TCO Thermique (%)", "TCO Nucléaire (%)",
    "TCO Eolien (%)", "TCO Hydraulique (%)", "TCO Solaire (%)", "TCO Bioénergies (%)",
]
REGIONS = ["Île-de-France", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine"]
MIN_DATE = "2021-01-01"

def main():
    chunks = []
    reader = pd.read_csv(SRC, sep=";", usecols=COLUMNS, parse_dates=["Date"], chunksize=200_000, low_memory=False)
    for chunk in reader:
        chunk = chunk[chunk["Région"].isin(REGIONS) & (chunk["Date"] >= MIN_DATE)]
        if not chunk.empty:
            chunks.append(chunk)
    sample = pd.concat(chunks, ignore_index=True)
    sample.to_csv(DST, sep=";", index=False)
    print(f"Wrote {len(sample)} rows to {DST}")

if __name__ == "__main__":
    main()
