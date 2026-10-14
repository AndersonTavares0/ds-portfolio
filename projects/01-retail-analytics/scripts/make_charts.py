#!/usr/bin/env python
"""Render the charts used by the Project 01 reports.

The charts are written as committed PNGs rather than generated during the site
build. That is deliberate: the publish workflow has no database and no dataset,
so anything the site needs to display has to already exist in the repository.

Run it with `uv run python tasks.py charts`, which is what sets `PYTHONPATH` so
that `retail` is importable.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file directly, before the package is installed.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from retail.config import REPO_ROOT, get_settings  # noqa: E402
from retail.io import build_engine  # noqa: E402

FIGURES_DIR = REPO_ROOT / "site" / "reports" / "01-retail-analytics" / "figures"

# One place for the palette, so every chart in the report looks like it belongs
# to the same document.
PRIMARY = "#1f6fb2"
ACCENT = "#d97706"
MUTED = "#b9c2cb"
INK = "#1f2933"

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.labelsize": 10,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": MUTED,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": MUTED,
        "grid.alpha": 0.35,
        "grid.linewidth": 0.6,
        "figure.autolayout": False,
    }
)


def save(fig: plt.Figure, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


def read(engine, sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, engine)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def chart_revenue_monthly(engine) -> None:
    """Monthly revenue, with the two partial months called out rather than hidden."""
    df = read(
        engine,
        """
        select month, orders, revenue_brl
        from analytics_marts.mart_revenue_monthly
        order by month
        """,
    )
    df["month"] = pd.to_datetime(df["month"])
    df["label"] = df["month"].dt.strftime("%b %Y")

    # The dataset ends mid-October 2018, so the final two months are incomplete.
    # Colouring them differently is the whole point of the chart: reading them as
    # a collapse would be a mistake, and a chart that hides that invites it.
    partial = df["month"] >= pd.Timestamp("2018-09-01")
    colours = [MUTED if is_partial else PRIMARY for is_partial in partial]

    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(df["label"], df["revenue_brl"] / 1_000, color=colours)
    ax.set_ylabel("Revenue (thousands of R$)")
    ax.set_title("Monthly revenue — September 2016 to October 2018")
    ax.tick_params(axis="x", rotation=90)

    # Headroom above the tallest bar, so the annotation can sit above the peak
    # instead of across it.
    peak_thousands = df["revenue_brl"].max() / 1_000
    ax.set_ylim(0, peak_thousands * 1.18)

    peak = df["revenue_brl"].idxmax()
    ax.annotate(
        "Black Friday",
        xy=(peak, peak_thousands),
        xytext=(peak - 4.2, peak_thousands * 1.06),
        ha="center",
        arrowprops={"arrowstyle": "->", "color": ACCENT, "lw": 1.4},
        color=ACCENT,
        fontweight="bold",
    )
    ax.text(
        0.02,
        0.97,
        "grey = incomplete month\n(dataset ends 17 Oct 2018)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=INK,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#f2f5f8", "edgecolor": MUTED},
    )
    save(fig, "revenue-monthly.png")


def chart_top_categories(engine) -> None:
    """The categories that carry the revenue."""
    df = read(
        engine,
        """
        select category, revenue_brl, avg_item_price_brl
        from analytics_marts.mart_category_revenue
        order by revenue_brl desc
        limit 12
        """,
    ).iloc[::-1]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.barh(df["category"], df["revenue_brl"] / 1_000, color=PRIMARY)
    ax.set_xlabel("Item revenue (thousands of R$)")
    ax.set_title("Top 12 categories by item revenue")
    ax.grid(axis="y", visible=False)

    for y, (value, price) in enumerate(
        zip(df["revenue_brl"], df["avg_item_price_brl"], strict=True)
    ):
        ax.text(
            value / 1_000 + 12,
            y,
            f"avg item R$ {price:,.0f}",
            va="center",
            fontsize=8,
            color=INK,
        )
    ax.margins(x=0.18)
    save(fig, "top-categories.png")


def chart_delivery_review(engine) -> None:
    """The strongest relationship in the dataset, in one picture."""
    df = read(
        engine,
        """
        select delivery_bucket, bucket_order, orders, pct_of_orders,
               avg_review_score, pct_review_score_le2
        from analytics_marts.mart_delivery_performance
        order by bucket_order
        """,
    )

    # The bucket names are precise but far too long to sit side by side as axis
    # labels, so they are wrapped for display. The colour still keys off the real
    # name, not the label.
    display = {
        "on time": "on time",
        "late: up to 7 days": "late\n0-7 days",
        "late: 8 to 14 days": "late\n8-14 days",
        "late: more than 14 days": "late\n>14 days",
        "never delivered": "never\ndelivered",
    }

    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.bar(
        [display[b] for b in df["delivery_bucket"]],
        df["avg_review_score"],
        color=[PRIMARY if b == "on time" else ACCENT for b in df["delivery_bucket"]],
    )
    ax.set_ylabel("Average review score")
    ax.set_ylim(0, 5)
    ax.set_title("Late delivery is where satisfaction goes")
    ax.grid(axis="x", visible=False)

    for bar, score, bad in zip(
        bars, df["avg_review_score"], df["pct_review_score_le2"], strict=True
    ):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            score + 0.1,
            f"{score:.2f}",
            ha="center",
            fontweight="bold",
            fontsize=10,
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            0.18,
            f"{bad:.0f}%\nscore ≤2",
            ha="center",
            fontsize=8,
            color="white",
        )
    ax.text(
        0.5,
        -0.32,
        "Bars show the mean score; the label inside each bar is the share of "
        "that group giving 1 or 2 stars.",
        transform=ax.transAxes,
        ha="center",
        fontsize=8.5,
        color=INK,
    )
    save(fig, "delivery-review.png")


def chart_late_by_state(engine) -> None:
    """Lateness is geographic, and it is not a small difference."""
    df = read(
        engine,
        """
        select customer_state, delivered_orders, late_orders, late_pct
        from analytics_marts.mart_late_delivery_by_state
        where delivered_orders >= 1000
        order by late_pct
        """,
    )

    fig, ax = plt.subplots(figsize=(8, 5.2))
    colours = [PRIMARY if s == "SP" else ACCENT for s in df["customer_state"]]
    ax.barh(df["customer_state"], df["late_pct"], color=colours)
    ax.set_xlabel("Deliveries arriving after the promised date (%)")
    ax.set_title("Late delivery by state — states with at least 1,000 deliveries")
    ax.grid(axis="y", visible=False)

    for y, (pct, orders) in enumerate(zip(df["late_pct"], df["delivered_orders"], strict=True)):
        ax.text(pct + 0.18, y, f"{pct:.1f}%  ({orders:,})", va="center", fontsize=8.5)
    ax.margins(x=0.22)
    save(fig, "late-by-state.png")


def chart_cohort_retention(engine) -> None:
    """Retention does not decay from a high base — it starts low and stays there."""
    df = read(
        engine,
        """
        -- `mart_cohort_retention` holds one row per (cohort_month, month_offset),
        -- so the cohorts must be summed before they can be plotted. Selecting the
        -- raw rows instead draws ~20 bars on top of each other at every offset,
        -- and the y-axis is then driven by whichever small cohort happens to have
        -- the highest retention. That is exactly what this chart did until the
        -- picture made it obvious.
        select month_offset,
               round(100.0 * sum(active_customers) / sum(cohort_customers), 2) as retention_pct
        from analytics_marts.mart_cohort_retention
        where month_offset between 1 and 12
        group by month_offset
        order by month_offset
        """,
    )

    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.bar(df["month_offset"].astype(str), df["retention_pct"], color=PRIMARY, width=0.62)
    ax.set_xlabel("Months after the customer's first order")
    ax.set_ylabel("Customers who ordered again (%)")
    ax.set_title("Cohort retention — month 0 is 100% by construction and is omitted")
    ax.grid(axis="x", visible=False)

    for x, pct in zip(df["month_offset"].astype(str), df["retention_pct"], strict=True):
        # Offset the label in points, not in data units: every value here is
        # under 1%, so a data-unit offset puts the text back on the bar's top
        # edge and reads as though it has been struck through.
        ax.annotate(
            f"{pct:.2f}",
            (x, pct),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=8,
        )
    ax.margins(y=0.22)
    ax.text(
        0.5,
        -0.34,
        "Flat, not declining. There is almost no repeat-purchase habit to lose — "
        "which is a different problem from the one retention programmes solve.",
        transform=ax.transAxes,
        ha="center",
        fontsize=8.5,
        color=INK,
    )
    save(fig, "cohort-retention.png")


def chart_repeat_purchase(engine) -> None:
    """The number that reframes the whole analysis."""
    df = read(
        engine,
        """
        select frequency, count(*) as customers
        from analytics_marts.mart_rfm
        group by frequency
        order by frequency
        """,
    )
    df["bucket"] = df["frequency"].map(lambda n: str(n) if n <= 4 else "5+")
    grouped = df.groupby("bucket", sort=False)["customers"].sum()

    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    bars = ax.bar(grouped.index, grouped.values, color=[ACCENT] + [PRIMARY] * (len(grouped) - 1))
    ax.set_yscale("log")
    ax.set_ylabel("Customers (log scale)")
    ax.set_xlabel("Orders placed")
    ax.set_title("How often a customer comes back")
    ax.grid(axis="x", visible=False)

    total = grouped.sum()
    for bar, value in zip(bars, grouped.values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.25,
            f"{value:,}\n{100 * value / total:.2f}%",
            ha="center",
            fontsize=8.5,
        )
    ax.margins(y=0.35)
    save(fig, "repeat-purchase.png")


def chart_order_status(engine) -> None:
    """What the revenue figure includes, so nobody has to assume."""
    df = read(
        engine,
        """
        select order_status, count(*) as orders, sum(order_value) as revenue
        from analytics_marts.fct_orders
        group by order_status
        order by revenue desc
        """,
    )
    df["revenue"] = df["revenue"].fillna(0)
    cancelled = df["order_status"].isin(["canceled", "unavailable"])

    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.barh(
        df["order_status"],
        df["revenue"] / 1_000,
        color=[ACCENT if is_cancelled else PRIMARY for is_cancelled in cancelled],
    )
    ax.set_xscale("log")
    ax.set_xlabel("Revenue recorded (thousands of R$, log scale)")
    ax.set_title("Revenue by order status")
    ax.grid(axis="y", visible=False)
    ax.text(
        0.99,
        0.97,
        "amber = cancelled or unavailable: R$ 269.7k, included in the\n"
        "revenue figure because a payment was recorded",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#f2f5f8", "edgecolor": MUTED},
    )
    save(fig, "order-status.png")


CHARTS = (
    chart_revenue_monthly,
    chart_top_categories,
    chart_delivery_review,
    chart_late_by_state,
    chart_cohort_retention,
    chart_repeat_purchase,
    chart_order_status,
)


def main() -> int:
    settings = get_settings()
    engine = build_engine(settings)
    print(f"writing charts to {FIGURES_DIR.relative_to(REPO_ROOT)}")
    for chart in CHARTS:
        chart(engine)
    print(f"done. {len(CHARTS)} charts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
