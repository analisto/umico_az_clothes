# -*- coding: utf-8 -*-
"""
Generate 10 business analytics charts for umico.az clothing marketplace.
Output: charts/01_category_volume.png  ...  charts/10_seller_concentration.png

Usage:
    python scripts/generate_charts.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless, safe on all platforms

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "clothes.csv"
CHARTS_DIR = ROOT / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Brand palette ─────────────────────────────────────────────────────────────
PRIMARY   = "#2E4057"   # dark navy   – dominant bars
ACCENT    = "#048A81"   # teal        – secondary / highlights
HIGHLIGHT = "#E76F51"   # coral       – alert / emphasis

# ── Category name translations ────────────────────────────────────────────────
CATEGORY_MAP = {
    "Ciyin cantalar":                              "Shoulder Bags",
    "Pul kiseleri, pulqabilar":                    "Wallets & Purses",
    "Qadin gun eyneклери":                         "Women's Sunglasses",
    "Kisi krosovkalari ve kedleri":                "Men's Sneakers",
    "Kisi gun eyneклери":                          "Men's Sunglasses",
    "Kross-bodi cantalar":                         "Crossbody Bags",
    "Qadin krosovkalari ve kedleri":               "Women's Sneakers",
    "Kisi cinsleri":                               "Men's Jeans",
    "Kisi klassik ayaqqabilar":                    "Men's Dress Shoes",
    "Kolqotqalar ve uzun corablar":                "Tights & Long Socks",
    "Camadanlar":                                  "Suitcases / Luggage",
    "Qadin serferleri":                            "Women's Scarves",
    "Bel cantalar, portfeller, mekteb cantalar":   "Backpacks & School Bags",
    "Qadin nazik koyneклери":                      "Women's Blouses",
    "Saclar ucun sancaqlar ve rezin baglari":      "Hair Clips & Bands",
    # Unicode originals (matched exactly as they appear in CSV)
    "\u00c7iyin \u00e7antal\u0131":                "Shoulder Bags",
}

# Build the full UTF-8 category map separately to avoid encoding issues
_CATEGORY_MAP_UTF8 = {
    "Çiyin çantaları":                              "Shoulder Bags",
    "Pul kisələri, pulqabıları":                    "Wallets & Purses",
    "Qadın gün eynəkləri":                          "Women's Sunglasses",
    "Kişi krosovkaları və kedləri":                 "Men's Sneakers",
    "Kişi gün eynəkləri":                           "Men's Sunglasses",
    "Kross-bodi çantalar":                          "Crossbody Bags",
    "Qadın krosovkaları və kedləri":                "Women's Sneakers",
    "Kişi cinsləri":                                "Men's Jeans",
    "Kişi klassik ayaqqabıları":                    "Men's Dress Shoes",
    "Kolqotqalar və uzun corablar":                 "Tights & Long Socks",
    "Çamadanlar":                                   "Suitcases / Luggage",
    "Qadın şərfləri":                               "Women's Scarves",
    "Bel çantaları, portfellər, məktəb çantaları":  "Backpacks & School Bags",
    "Qadın nazik köynəkləri":                       "Women's Blouses",
    "Saçlar üçün sancaqlar və rezin bağları":       "Hair Clips & Bands",
}

DISC_TIER_ORDER = ["No Discount", "1-10%", "11-24%", "25-50%", "50%+"]
PRICE_TIER_ORDER = ["Under 10", "10-25", "25-50", "50-100", "100-200", "200+"]


# ── Data Loading ──────────────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, encoding="utf-8")

    # English category names
    df["category_en"] = df["category_name"].map(_CATEGORY_MAP_UTF8).fillna(df["category_name"])

    # Price tiers
    price_bins = [0, 10, 25, 50, 100, 200, float("inf")]
    df["price_tier"] = pd.cut(
        df["retail_price"],
        bins=price_bins,
        labels=PRICE_TIER_ORDER,
    )

    # Discount tiers
    def _disc_tier(d):
        if d == 0:      return "No Discount"
        elif d <= 10:   return "1-10%"
        elif d < 25:    return "11-24%"
        elif d <= 50:   return "25-50%"
        else:           return "50%+"

    df["disc_tier"] = df["discount_pct"].apply(_disc_tier)

    # Brand flag: True = has a real brand name
    df["has_brand"] = ~df["brand"].isin(["No Brand", "No brand", "", "nan"]) & df["brand"].notna()

    # Review flag: True = product has at least one review
    df["has_review"] = df["rating_value"] > 0

    return df


# ── Style ─────────────────────────────────────────────────────────────────────

def apply_style() -> None:
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        plt.rcParams["axes.grid"] = True
        plt.rcParams["grid.color"] = "#eeeeee"
        plt.rcParams["axes.facecolor"] = "white"

    plt.rcParams.update({
        "font.family":        "DejaVu Sans",
        "axes.titlesize":     13,
        "axes.titleweight":   "bold",
        "axes.labelsize":     11,
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "figure.dpi":         100,
    })


# ── Save Helper ───────────────────────────────────────────────────────────────

def save_fig(fig: plt.Figure, filename: str) -> None:
    out = CHARTS_DIR / filename
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {filename}")


# ── Chart 01: Top 15 Categories by Product Volume ─────────────────────────────

def chart_01(df: pd.DataFrame) -> None:
    top15 = (
        df.groupby("category_en")
          .size()
          .sort_values(ascending=False)
          .head(15)
          .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = [ACCENT if i >= 12 else PRIMARY for i in range(len(top15))]
    bars = ax.barh(top15.index, top15.values, color=colors, height=0.65)

    for bar, val in zip(bars, top15.values):
        ax.text(
            bar.get_width() + 55,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}",
            va="center", ha="left", fontsize=9, color="#555555",
        )

    ax.set_xlabel("Number of Products", labelpad=8)
    ax.set_title(
        "Shoulder Bags Lead the Catalog With 5,627 Listings\n"
        "Top 15 Categories by Product Volume",
        pad=14,
    )
    ax.set_xlim(0, top15.max() * 1.18)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save_fig(fig, "01_category_volume.png")


# ── Chart 02: Price Architecture ──────────────────────────────────────────────

def chart_02(df: pd.DataFrame) -> None:
    counts = df["price_tier"].value_counts().reindex(PRICE_TIER_ORDER)
    total = counts.sum()
    percentages = (counts / total * 100).round(1)

    colors = [ACCENT if t == "25-50" else PRIMARY for t in PRICE_TIER_ORDER]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(PRICE_TIER_ORDER, counts.values, color=colors, width=0.6)

    for bar, pct in zip(bars, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 280,
            f"{pct}%",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    ax.set_xlabel("Price Range (AZN)", labelpad=8)
    ax.set_ylabel("Number of Products", labelpad=8)
    ax.set_title(
        "The 25-50 AZN Band Captures 35% of All Listings\n"
        "Price Tier Distribution Across 62,633 Products",
        pad=14,
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save_fig(fig, "02_price_architecture.png")


# ── Chart 03: Discount Landscape ──────────────────────────────────────────────

def chart_03(df: pd.DataFrame) -> None:
    counts = df["disc_tier"].value_counts().reindex(DISC_TIER_ORDER)
    total = counts.sum()
    percentages = (counts / total * 100).round(1)

    color_map = {
        "No Discount": PRIMARY,
        "1-10%":       HIGHLIGHT,
        "11-24%":      PRIMARY,
        "25-50%":      ACCENT,
        "50%+":        PRIMARY,
    }
    colors = [color_map[t] for t in DISC_TIER_ORDER]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(DISC_TIER_ORDER, counts.values, color=colors, width=0.6)

    for bar, pct in zip(bars, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 180,
            f"{pct}%",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    ax.set_xlabel("Discount Tier", labelpad=8)
    ax.set_ylabel("Number of Products", labelpad=8)
    ax.set_title(
        "Discount Strategy Skews Extreme - The Moderate Middle Is Nearly Absent\n"
        "Products by Discount Tier",
        pad=14,
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    idx_moderate = DISC_TIER_ORDER.index("1-10%")
    bar_moderate = bars[idx_moderate]
    moderate_count = counts["1-10%"]
    ax.annotate(
        "Only 1.6% of products\noffer a moderate discount",
        xy=(bar_moderate.get_x() + bar_moderate.get_width() / 2, moderate_count),
        xytext=(1.8, moderate_count + 5500),
        fontsize=9, color=HIGHLIGHT,
        arrowprops=dict(arrowstyle="->", color=HIGHLIGHT, lw=1.2),
    )

    save_fig(fig, "03_discount_landscape.png")


# ── Chart 04: Average Price by Category ───────────────────────────────────────

def chart_04(df: pd.DataFrame) -> None:
    top15_cats = (
        df.groupby("category_en")
          .size()
          .sort_values(ascending=False)
          .head(15)
          .index
    )
    avg_prices = (
        df[df["category_en"].isin(top15_cats)]
          .groupby("category_en")["retail_price"]
          .mean()
          .sort_values(ascending=True)
    )

    colors = [HIGHLIGHT if v >= 100 else ACCENT for v in avg_prices.values]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(avg_prices.index, avg_prices.values, color=colors, height=0.65)

    for bar, val in zip(bars, avg_prices.values):
        ax.text(
            bar.get_width() + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.0f} AZN",
            va="center", ha="left", fontsize=9,
        )

    overall_median = df["retail_price"].median()
    ax.axvline(
        overall_median,
        color="#999999", linestyle="--", lw=1.3,
        label=f"Catalog median: {overall_median:.0f} AZN",
    )
    ax.legend(fontsize=9, loc="lower right")

    ax.set_xlabel("Average Retail Price (AZN)", labelpad=8)
    ax.set_title(
        "Suitcases and Dress Shoes Command the Highest Prices\n"
        "Average Price Across Top 15 Categories",
        pad=14,
    )
    ax.set_xlim(0, avg_prices.max() * 1.22)

    save_fig(fig, "04_category_pricing.png")


# ── Chart 05: Installment Plan Distribution ────────────────────────────────────

def chart_05(df: pd.DataFrame) -> None:
    month_order = [0, 3, 6, 12, 18, 24]
    label_map = {0: "None", 3: "3 mo", 6: "6 mo", 12: "12 mo", 18: "18 mo", 24: "24 mo"}
    counts = df["max_installment_months"].value_counts().reindex(month_order, fill_value=0)
    labels = [label_map[m] for m in month_order]
    total = counts.sum()
    percentages = (counts / total * 100).round(1)

    colors = [
        HIGHLIGHT if m == 0 else (ACCENT if m == 18 else PRIMARY)
        for m in month_order
    ]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(labels, counts.values, color=colors, width=0.6)

    for bar, pct in zip(bars, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 350,
            f"{pct}%",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    ax.set_xlabel("Maximum Installment Term", labelpad=8)
    ax.set_ylabel("Number of Products", labelpad=8)
    ax.set_title(
        "18-Month Installment Dominates - 75% of Products Offer the Longest Term\n"
        "Installment Plan Distribution Across the Catalog",
        pad=14,
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save_fig(fig, "05_installment_plans.png")


# ── Chart 06: Top 10 Sellers ──────────────────────────────────────────────────

def chart_06(df: pd.DataFrame) -> None:
    seller_stats = (
        df.groupby("seller_name")
          .agg(count=("id", "count"), rating=("seller_rating", "first"))
          .sort_values("count", ascending=False)
          .head(10)
          .sort_values("count", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(14, 7))
    bar_colors = [
        HIGHLIGHT if row["rating"] < 90 else PRIMARY
        for _, row in seller_stats.iterrows()
    ]
    bars = ax.barh(seller_stats.index, seller_stats["count"], color=bar_colors, height=0.65)

    for bar, (name, row) in zip(bars, seller_stats.iterrows()):
        # Count label outside bar
        ax.text(
            bar.get_width() + 30,
            bar.get_y() + bar.get_height() / 2,
            f"{int(row['count']):,}",
            va="center", ha="left", fontsize=9,
        )
        # Rating badge inside bar
        if bar.get_width() > 400:
            badge_color = "#54C6BE" if row["rating"] >= 95 else "#FFAA88"
            ax.text(
                70,
                bar.get_y() + bar.get_height() / 2,
                f"Rating: {int(row['rating'])}",
                va="center", ha="left", fontsize=8.5,
                color="white", fontweight="bold",
            )

    ax.set_xlabel("Number of Products Listed", labelpad=8)
    ax.set_title(
        "Top 10 Sellers Control 33% of the Catalog - Most With Near-Perfect Ratings\n"
        "Product Volume and Seller Rating for Top 10 Sellers",
        pad=14,
    )
    ax.set_xlim(0, seller_stats["count"].max() * 1.18)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save_fig(fig, "06_top_sellers.png")


# ── Chart 07: Brand Attribution ───────────────────────────────────────────────

def chart_07(df: pd.DataFrame) -> None:
    no_brand_count = (~df["has_brand"]).sum()
    named_brand_count = df["has_brand"].sum()
    brand_counts = pd.Series({"No Brand": no_brand_count, "Named Brand": named_brand_count})

    top10_brands = (
        df[df["has_brand"]]
          .groupby("brand")
          .size()
          .sort_values(ascending=False)
          .head(10)
          .sort_values(ascending=True)
    )

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14, 7))
    fig.suptitle(
        "72% of Products Carry No Brand - A Critical Catalog Trust Gap",
        fontsize=13, fontweight="bold", y=1.01,
    )

    # Left panel: branded vs no-brand
    colors_left = [HIGHLIGHT, ACCENT]
    bars_l = ax_left.bar(brand_counts.index, brand_counts.values, color=colors_left, width=0.5)
    for bar, val in zip(bars_l, brand_counts.values):
        pct = val / len(df) * 100
        ax_left.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            f"{val:,}\n({pct:.0f}%)",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )
    ax_left.set_ylabel("Number of Products")
    ax_left.set_title("Brand Attribution", fontsize=12)
    ax_left.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax_left.spines["top"].set_visible(False)
    ax_left.spines["right"].set_visible(False)

    # Right panel: top 10 named brands
    ax_right.barh(top10_brands.index, top10_brands.values, color=PRIMARY, height=0.65)
    for i, (name, val) in enumerate(top10_brands.items()):
        ax_right.text(
            val + 20, i,
            f"{val:,}",
            va="center", ha="left", fontsize=9,
        )
    ax_right.set_xlabel("Number of Products")
    ax_right.set_title("Top 10 Named Brands", fontsize=12)
    ax_right.set_xlim(0, top10_brands.max() * 1.18)
    ax_right.spines["top"].set_visible(False)
    ax_right.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, "07_brand_attribution.png")


# ── Chart 08: Review Coverage ─────────────────────────────────────────────────

def chart_08(df: pd.DataFrame) -> None:
    top10_cats = (
        df.groupby("category_en")
          .size()
          .sort_values(ascending=False)
          .head(10)
          .index
    )

    sub = df[df["category_en"].isin(top10_cats)].copy()

    cat_order = (
        df.groupby("category_en")
          .size()
          .reindex(top10_cats)
          .sort_values(ascending=True)
          .index
    )

    pivot = (
        sub.groupby("category_en")["has_review"]
           .agg(reviewed="sum", total="count")
           .assign(not_reviewed=lambda x: x["total"] - x["reviewed"])
           .reindex(cat_order)
    )

    fig, ax = plt.subplots(figsize=(13, 7))
    ax.barh(
        pivot.index, pivot["not_reviewed"],
        color=PRIMARY, height=0.65, label="No Review",
    )
    ax.barh(
        pivot.index, pivot["reviewed"],
        color=ACCENT, height=0.65, left=pivot["not_reviewed"], label="Has Review",
    )

    for i, (name, row) in enumerate(pivot.iterrows()):
        pct = row["reviewed"] / row["total"] * 100
        ax.text(
            row["total"] + 45, i,
            f"{pct:.1f}% reviewed  ({int(row['reviewed']):,})",
            va="center", ha="left", fontsize=8.5, color="#444444",
        )

    ax.set_xlabel("Number of Products", labelpad=8)
    ax.set_title(
        "Fewer Than 3% of Products Have Any Customer Review\n"
        "Review Coverage by Category (Top 10 Categories)",
        pad=14,
    )
    ax.set_xlim(0, pivot["total"].max() * 1.38)
    ax.legend(loc="lower right", fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    save_fig(fig, "08_review_coverage.png")


# ── Chart 09: Discount vs Price Relationship ──────────────────────────────────

def chart_09(df: pd.DataFrame) -> None:
    grp = (
        df.groupby("disc_tier")
          .agg(avg_price=("retail_price", "mean"), count=("id", "count"))
          .reindex(DISC_TIER_ORDER)
    )

    x = np.arange(len(DISC_TIER_ORDER))
    width = 0.38

    fig, ax1 = plt.subplots(figsize=(13, 7))
    ax2 = ax1.twinx()

    # Volume bars on secondary axis (background, behind)
    ax2.bar(
        x - width / 2, grp["count"],
        width=width, color=PRIMARY, alpha=0.30,
        label="Product Count (right axis)",
    )
    ax2.set_ylabel("Number of Products", color="#888888", labelpad=8)
    ax2.tick_params(axis="y", labelcolor="#888888")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    # Avg price bars on primary axis (foreground)
    price_bars = ax1.bar(
        x + width / 2, grp["avg_price"],
        width=width, color=ACCENT,
        label="Avg Retail Price (left axis)",
    )
    ax1.set_ylabel("Average Retail Price (AZN)", color=ACCENT, labelpad=8)
    ax1.tick_params(axis="y", labelcolor=ACCENT)

    for bar, val in zip(price_bars, grp["avg_price"]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{val:.0f} AZN",
            ha="center", va="bottom", fontsize=9, color=ACCENT, fontweight="bold",
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(DISC_TIER_ORDER)
    ax1.set_title(
        "Higher Discounts Do Not Target Higher-Priced Products\n"
        "Average Retail Price and Product Volume by Discount Tier",
        pad=14,
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)

    save_fig(fig, "09_discount_price_relationship.png")


# ── Chart 10: Seller Market Concentration ─────────────────────────────────────

def chart_10(df: pd.DataFrame) -> None:
    seller_counts = df.groupby("seller_name").size().sort_values(ascending=False)
    total = len(df)
    milestones = [5, 10, 15, 20, 25, 50]
    cumulative = [seller_counts.head(n).sum() / total * 100 for n in milestones]
    labels = [f"Top {n}" for n in milestones]
    colors = [HIGHLIGHT if n <= 10 else PRIMARY for n in milestones]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(labels, cumulative, color=colors, width=0.55)

    for bar, pct in zip(bars, cumulative):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.6,
            f"{pct:.1f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
        )

    ax.axhline(50, color="#999999", linestyle="--", lw=1.3, label="50% concentration threshold")
    ax.set_ylim(0, 88)
    ax.set_xlabel("Seller Cohort (by Rank)", labelpad=8)
    ax.set_ylabel("Cumulative Share of Total Catalog (%)", labelpad=8)
    ax.set_title(
        "25 Sellers Control Nearly Half of 62,633 Listings\n"
        "Cumulative Catalog Share by Top Seller Cohorts  (787 Total Sellers)",
        pad=14,
    )
    ax.legend(fontsize=9)

    save_fig(fig, "10_seller_concentration.png")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading data ...")
    df = load_data()
    print(f"  {len(df):,} products loaded.")
    apply_style()

    chart_fns = [
        ("01_category_volume",            chart_01),
        ("02_price_architecture",          chart_02),
        ("03_discount_landscape",          chart_03),
        ("04_category_pricing",            chart_04),
        ("05_installment_plans",           chart_05),
        ("06_top_sellers",                 chart_06),
        ("07_brand_attribution",           chart_07),
        ("08_review_coverage",             chart_08),
        ("09_discount_price_relationship", chart_09),
        ("10_seller_concentration",        chart_10),
    ]

    print(f"\nGenerating {len(chart_fns)} charts ...")
    for name, fn in chart_fns:
        fn(df)

    print(f"\nDone. All charts saved to: charts/")


if __name__ == "__main__":
    main()
