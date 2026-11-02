import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr
from wordcloud import WordCloud

FIG = Path("figures")
FIG.mkdir(exist_ok=True)
sns.set_theme(style="whitegrid")

BAND_ORDER = ["Budget (up to 300)", "Mid (301-600)",
              "Upper-mid (601-1000)", "Premium (1000+)"]


def save(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=150, bbox_inches="tight")
    plt.close()


def explode_csv(d, col):
    out = d.dropna(subset=[col]).copy()
    out[col] = out[col].str.split(",")
    out = out.explode(col)
    out[col] = out[col].str.strip()
    return out[out[col] != ""]


def cloud(freq, title, fname):
    wc = WordCloud(width=1000, height=500, background_color="white")
    wc = wc.generate_from_frequencies({k: int(v) for k, v in freq.items()})
    plt.figure(figsize=(12, 6))
    plt.imshow(wc)
    plt.axis("off")
    plt.title(title)
    save(fname)


def main():
    df = pd.read_csv("data/processed/zomato_cleaned.csv")
    rated = df[df["rate"].notna()].copy()
    S = {
        "n_restaurants": int(len(df)),
        "n_rated": int(len(rated)),
        "mean_rating": round(float(rated["rate"].mean()), 2),
        "median_cost_inr": float(df["cost_inr"].median()),
    }

    # 1. overview
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(rated["rate"], bins=25, kde=True, ax=ax[0])
    ax[0].set_title("Rating distribution (rated restaurants only)")
    df["rest_type"].value_counts().head(10).plot.barh(ax=ax[1], color="steelblue")
    ax[1].invert_yaxis()
    ax[1].set_title("Most common restaurant types")
    save("overview.png")

    # 2. cuisines
    cu_rated = explode_csv(rated, "cuisines")
    cs = cu_rated.groupby("cuisines").agg(n=("name", "count"), avg_rating=("rate", "mean"))
    eligible = cs[cs.n >= 30]
    best = eligible.sort_values("avg_rating", ascending=False)
    cu_all = explode_csv(df, "cuisines")
    common = cu_all["cuisines"].value_counts()

    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    best.head(15)["avg_rating"].plot.barh(ax=ax[0], color="seagreen")
    ax[0].invert_yaxis()
    ax[0].set_title("Highest-rated cuisines (at least 30 restaurants)")
    ax[0].set_xlim(best["avg_rating"].head(15).min() - 0.1, best["avg_rating"].max() + 0.05)
    common.head(15).plot.barh(ax=ax[1], color="steelblue")
    ax[1].invert_yaxis()
    ax[1].set_title("Most common cuisines")
    save("cuisine.png")

    cloud(common.head(150).to_dict(), "Popular cuisines", "wordcloud_cuisines.png")

    dishes = explode_csv(df, "dish_liked")
    dishes["dish_liked"] = dishes["dish_liked"].str.title()
    dish_counts = dishes["dish_liked"].value_counts()
    cloud(dish_counts.head(150).to_dict(), "Most-liked dishes (from Zomato dish_liked)",
          "wordcloud_dishes.png")

    S["top_rated_cuisines"] = [(k, round(float(v), 2)) for k, v in best["avg_rating"].head(5).items()]
    S["most_common_cuisines"] = [(k, int(v)) for k, v in common.head(5).items()]
    gap = eligible[eligible.n <= eligible.n.median()].sort_values("avg_rating", ascending=False).head(5)
    S["gap_cuisines"] = [(k, round(float(r.avg_rating), 2), int(r.n)) for k, r in gap.iterrows()]
    S["top_dishes"] = [(k, int(v)) for k, v in dish_counts.head(8).items()]

    # 3. locations
    hot = df["location"].value_counts().head(15)
    loc = rated.groupby("location").agg(n=("name", "count"), avg=("rate", "mean"))
    best_loc = loc[loc.n >= 30].sort_values("avg", ascending=False).head(15)

    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    hot.plot.barh(ax=ax[0], color="steelblue")
    ax[0].invert_yaxis()
    ax[0].set_title("Hotspots: locations with most restaurants")
    best_loc["avg"].plot.barh(ax=ax[1], color="seagreen")
    ax[1].invert_yaxis()
    ax[1].set_title("Highest-rated locations (at least 30 rated)")
    ax[1].set_xlim(best_loc["avg"].min() - 0.1, best_loc["avg"].max() + 0.05)
    save("locations.png")

    S["top_hotspots"] = [(k, int(v)) for k, v in hot.head(5).items()]
    S["top_rated_locations"] = [(k, round(float(r.avg), 2), int(r.n)) for k, r in best_loc.head(5).iterrows()]

    top_loc = df["location"].value_counts().head(15).index
    top_rt = df["rest_type"].value_counts().head(8).index
    sub = rated[rated["location"].isin(top_loc) & rated["rest_type"].isin(top_rt)]
    pv = sub.pivot_table(index="location", columns="rest_type", values="rate", aggfunc="mean")
    cnt = sub.pivot_table(index="location", columns="rest_type", values="rate", aggfunc="count")
    pv = pv.where(cnt >= 5)
    plt.figure(figsize=(11, 7))
    sns.heatmap(pv, annot=True, fmt=".2f", cmap="YlGnBu", linewidths=0.5)
    plt.title("Average rating: location x restaurant type (cells with 5+ restaurants)")
    save("heatmap_loc_type.png")

    # 4. price vs rating
    pb = rated.dropna(subset=["price_band"])
    plt.figure(figsize=(7, 4))
    sns.boxplot(data=pb, x="price_band", y="rate", order=BAND_ORDER)
    plt.xticks(rotation=15)
    plt.title("Rating by price band (cost for two, INR)")
    save("price_box.png")

    num = rated[["rate", "votes", "cost_inr", "online_order", "book_table"]].dropna().copy()
    num["log_votes"] = np.log1p(num.pop("votes"))
    num["log_cost"] = np.log(num.pop("cost_inr"))
    plt.figure(figsize=(7, 5))
    sns.heatmap(num.corr(method="spearman"), annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Spearman correlation")
    save("corr.png")

    rc = rated.dropna(subset=["cost_inr"])
    S["rho_cost"] = round(float(spearmanr(rc["cost_inr"], rc["rate"])[0]), 2)
    rv = rated.dropna(subset=["votes"])
    S["rho_votes"] = round(float(spearmanr(rv["votes"], rv["rate"])[0]), 2)
    bands = pb.groupby("price_band")["rate"].mean()
    S["rating_by_band"] = {b: round(float(bands[b]), 2) for b in BAND_ORDER if b in bands.index}

    # 5. other factors
    for col in ["online_order", "book_table"]:
        g = rated.groupby(col)["rate"].mean()
        S[col] = {"no": round(float(g.get(0, np.nan)), 2), "yes": round(float(g.get(1, np.nan)), 2)}
    rt = rated.groupby("rest_type").agg(n=("name", "count"), avg=("rate", "mean"))
    rt = rt[rt.n >= 50].sort_values("avg", ascending=False).head(5)
    S["top_rest_types"] = [(k, round(float(r.avg), 2), int(r.n)) for k, r in rt.iterrows()]

    with open("data/processed/summary.json", "w", encoding="utf-8") as f:
        json.dump(S, f, indent=2)
    print(json.dumps(S, indent=2))


if __name__ == "__main__":
    main()