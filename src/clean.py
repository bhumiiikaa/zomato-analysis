import numpy as np
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/processed")

# APPROXIMATE: US dollars per 1 Indian rupee. Check today's rate (for example on xe.com)
# and write the source and date in your report.
USD_PER_INR = 0.0115

VALID_TYPES = ["Buffet", "Cafes", "Delivery", "Desserts", "Dine-out",
               "Drinks & nightlife", "Pubs and bars"]

BAND_LABELS = ["Budget (up to 300)", "Mid (301-600)",
               "Upper-mid (601-1000)", "Premium (1000+)"]


def load() -> pd.DataFrame:
    try:
        return pd.read_csv(RAW / "zomato.csv", encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(RAW / "zomato.csv", encoding="latin-1")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(" ", "_", regex=False))
    print("Columns found:", list(df.columns))

    cost_col = [c for c in df.columns if c.startswith("approx_cost")][0]
    df = df.rename(columns={cost_col: "cost_inr", "listed_in(type)": "listed_type"})

    # 1. remove broken rows (this file has rows where review text spilled into other columns)
    before = len(df)
    df = df[df["online_order"].isin(["Yes", "No"])]
    df = df[df["book_table"].isin(["Yes", "No"])]
    df = df[df["listed_type"].isin(VALID_TYPES)]
    print("Broken rows removed:", before - len(df))

    # 2. remove duplicates (the same restaurant is listed once per listing type)
    before = len(df)
    df = df.drop_duplicates(subset=["name", "address"])
    print("Duplicate rows removed:", before - len(df))

    # 3. text fields
    for c in ["name", "address", "location", "rest_type", "cuisines", "dish_liked"]:
        df[c] = df[c].str.strip()
    df["location"] = df["location"].fillna("Unknown")

    # 4. yes/no -> 1/0
    df["online_order"] = df["online_order"].map({"Yes": 1, "No": 0})
    df["book_table"] = df["book_table"].map({"Yes": 1, "No": 0})

    # 5. rating: "4.1/5" -> 4.1 ; "NEW" and "-" become empty (unrated, NOT filled in)
    df["rate"] = pd.to_numeric(
        df["rate"].astype(str).str.replace("/5", "", regex=False).str.strip(),
        errors="coerce")
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce")

    # 6. cost: "1,200" -> 1200, then convert to USD
    df["cost_inr"] = pd.to_numeric(
        df["cost_inr"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    df.loc[df["cost_inr"] <= 0, "cost_inr"] = np.nan
    df["cost_usd"] = (df["cost_inr"] * USD_PER_INR).round(2)
    df["price_band"] = pd.cut(df["cost_inr"], bins=[0, 300, 600, 1000, np.inf],
                              labels=BAND_LABELS)

    df["rated"] = df["rate"].notna()
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = clean(load())
    df.to_csv(OUT / "zomato_cleaned.csv", index=False)
    print("Saved", df.shape, "| rated:", int(df["rated"].sum()))


if __name__ == "__main__":
    main()