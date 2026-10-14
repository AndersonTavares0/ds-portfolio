#!/usr/bin/env python
"""Render the charts used by the Project 01 reports.

The charts are written as committed PNGs rather than generated during the site
build. That is deliberate: the publish workflow has no database and no dataset,
so anything the site needs to display has to already exist in the repository.

Every chart is drawn twice, once in English and once in Portuguese, because the
website is published in both languages and an English axis label inside a
Portuguese page reads as unfinished. The data is fetched once and only the
strings differ, so the two sets cannot drift apart.

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

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from retail.config import REPO_ROOT, get_settings  # noqa: E402
from retail.io import build_engine  # noqa: E402

# The English figures live at `figures/` and the Portuguese ones at `figures/pt/`,
# so the Portuguese reports climb one directory further. Keeping both under one
# figures directory means the two language builds share nothing but the data.
FIGURES_DIR = REPO_ROOT / "site" / "reports" / "01-retail-analytics" / "figures"
LANGS = ("en", "pt")

# One place for the palette, so every chart in the report looks like it belongs to
# the same document. These are the light values from `site/theme/theme.scss`; the dark
# bundle is only used for the page, and the figures keep their white ground.
PRIMARY = "#1f6fb2"
ACCENT = "#d97706"
MUTED = "#c4cdd5"
SOFT = "#6b7a88"
INK = "#1f2933"

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "sans-serif",
        # The first family matplotlib can find wins. DejaVu Sans ships with
        # matplotlib, so anything listed after it is unreachable — which is how
        # "Segoe UI" ended up dead code behind it, with every figure falling back
        # to DejaVu. Keep the always-present family last.
        "font.sans-serif": ["Source Sans 3", "Segoe UI", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12.5,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 12,
        "axes.titlecolor": INK,
        "axes.labelsize": 10,
        "axes.labelcolor": SOFT,
        "text.color": INK,
        "xtick.color": SOFT,
        "ytick.color": SOFT,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.edgecolor": MUTED,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": MUTED,
        "grid.alpha": 0.5,
        "grid.linewidth": 0.7,
        "figure.autolayout": False,
    }
)


# Every string a reader sees. Anything that is a value from the database — an
# order status, a state code, a category name — is deliberately absent: those are
# data, and translating them would break the link to the models and the raw
# tables. Only the labels the chart itself supplies are translated.
STRINGS = {
    "en": {
        "revenue_title": "Monthly revenue",
        "revenue_y": "Revenue (thousands of R$)",
        "revenue_note": "Edge months excluded (Sep 2016, Sep–Oct 2018): {orders} orders.",
        "black_friday": "Black Friday",
        "categories_title": "The 12 categories that carry the revenue",
        "categories_x": "Item revenue (thousands of R$)",
        "avg_item": "avg item R$ {value:,.0f}",
        "delivery_title": "Where satisfaction goes",
        "delivery_y": "Average review score",
        "share_le2": "{value:.0f}%\nscore ≤2",
        "buckets": {
            "on time": "on time",
            "late: up to 7 days": "late\n0-7 days",
            "late: 8 to 14 days": "late\n8-14 days",
            "late: more than 14 days": "late\n>14 days",
            "never delivered": "never\ndelivered",
        },
        "state_title": "Late delivery by state (states with at least 1,000 deliveries)",
        "state_x": "Deliveries arriving after the promised date (%)",
        "state_label": "{pct:.1f}% ({orders:,})",
        "cohort_title": "Retention after the first order",
        "cohort_x": "Months after the customer's first order",
        "cohort_y": "Customers who ordered again (%)",
        "repeat_title": "How often a customer comes back",
        "repeat_x": "Orders placed",
        "repeat_y": "Customers (log scale)",
        "status_title": "What the revenue figure includes",
        "status_x": "Revenue recorded (thousands of R$, log scale)",
        "status_note": (
            "Amber = cancelled or unavailable.\nA payment was recorded, so it is counted."
        ),
    },
    "pt": {
        "revenue_title": "Receita mensal",
        "revenue_y": "Receita (milhares de R$)",
        "revenue_note": "Meses de borda excluídos (set 2016, set–out 2018): {orders} pedidos.",
        "black_friday": "Black Friday",
        "categories_title": "As 12 categorias que sustentam a receita",
        "categories_x": "Receita de itens (milhares de R$)",
        "avg_item": "item médio R$ {value:,.0f}",
        "delivery_title": "Onde a satisfação cai",
        "delivery_y": "Nota média da avaliação",
        "share_le2": "{value:.0f}%\nnota ≤2",
        "buckets": {
            "on time": "no prazo",
            "late: up to 7 days": "atraso\n0-7 dias",
            "late: 8 to 14 days": "atraso\n8-14 dias",
            "late: more than 14 days": "atraso\n>14 dias",
            "never delivered": "nunca\nentregue",
        },
        "state_title": "Atraso na entrega por estado (estados com ao menos 1,000 entregas)",
        "state_x": "Entregas após a data prometida (%)",
        "state_label": "{pct:.1f}% ({orders:,})",
        "cohort_title": "Retenção após o primeiro pedido",
        "cohort_x": "Meses após o primeiro pedido do cliente",
        "cohort_y": "Clientes que compraram de novo (%)",
        "repeat_title": "Com que frequência o cliente volta",
        "repeat_x": "Pedidos feitos",
        "repeat_y": "Clientes (escala log)",
        "status_title": "O que a receita inclui",
        "status_x": "Receita registrada (milhares de R$, escala log)",
        "status_note": "Âmbar = cancelado ou indisponível.\nHouve pagamento, então entra na conta.",
    },
}


def read(engine, sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, engine)


def load_data(engine) -> dict[str, pd.DataFrame]:
    """Query every series once, so both language builds plot the same numbers."""
    return {
        "revenue": read(
            engine,
            """
            select month, orders, revenue_brl
            from analytics_marts.mart_revenue_monthly
            order by month
            """,
        ),
        "categories": read(
            engine,
            """
            select category, revenue_brl, avg_item_price_brl
            from analytics_marts.mart_category_revenue
            order by revenue_brl desc
            limit 12
            """,
        ),
        "delivery": read(
            engine,
            """
            select delivery_bucket, bucket_order, orders, pct_of_orders,
                   avg_review_score, pct_review_score_le2
            from analytics_marts.mart_delivery_performance
            order by bucket_order
            """,
        ),
        "states": read(
            engine,
            """
            select customer_state, delivered_orders, late_orders, late_pct
            from analytics_marts.mart_late_delivery_by_state
            where delivered_orders >= 1000
            order by late_pct
            """,
        ),
        "cohort": read(
            engine,
            """
            -- `mart_cohort_retention` holds one row per (cohort_month,
            -- month_offset), so the cohorts have to be summed before they can be
            -- plotted. Selecting the raw rows draws ~20 bars on top of each other
            -- at every offset, and the y-axis is then driven by whichever small
            -- cohort happens to have the highest retention.
            select month_offset,
                   round(100.0 * sum(active_customers) / sum(cohort_customers), 2) as retention_pct
            from analytics_marts.mart_cohort_retention
            where month_offset between 1 and 12
            group by month_offset
            order by month_offset
            """,
        ),
        "repeat": read(
            engine,
            """
            select frequency, count(*) as customers
            from analytics_marts.mart_rfm
            group by frequency
            order by frequency
            """,
        ),
        "status": read(
            engine,
            """
            select order_status, count(*) as orders, sum(order_value) as revenue
            from analytics_marts.fct_orders
            group by order_status
            order by revenue desc
            """,
        ),
    }


def save(fig: plt.Figure, lang: str, name: str) -> None:
    directory = FIGURES_DIR if lang == "en" else FIGURES_DIR / lang
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def chart_revenue_monthly(data, s, lang: str) -> None:
    """Monthly revenue over the period the marketplace was actually trading."""
    df = data["revenue"].copy()
    df["month"] = pd.to_datetime(df["month"])

    # Three months hold almost nothing: September 2016 (4 orders), and the two
    # months the dataset was cut off in, September and October 2018 (16 and 4). At
    # this scale their bars are invisible slivers — a chart cannot show 0.06% of
    # its own height. October 2016 (324 orders) and December 2016 (1 order) are
    # both kept: they are the marketplace's first months of trading, and a 1-order
    # bar is honest about how little was happening. The note below names exactly
    # which months were dropped, because a chart that colours a bar nobody can
    # see, or drops it silently, is worse than one that says what it left out.
    window = (df["month"] >= pd.Timestamp("2016-10-01")) & (
        df["month"] <= pd.Timestamp("2018-08-31")
    )
    excluded_orders = int(df.loc[~window, "orders"].sum())
    df = df.loc[window].copy()

    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    # Plotted against real dates rather than against a list of labels: the dataset
    # has no November 2016 at all, and a categorical axis would draw October and
    # December 2016 as adjacent bars, inventing a month that never existed.
    ax.bar(df["month"], df["revenue_brl"] / 1_000, color=PRIMARY, width=20)
    ax.set_ylabel(s["revenue_y"])
    ax.set_title(s["revenue_title"])
    ax.grid(axis="x", visible=False)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.tick_params(axis="x", rotation=90, labelsize=8)

    # Headroom above the tallest bar, so the annotation can sit above the peak
    # rather than across it.
    peak_thousands = df["revenue_brl"].max() / 1_000
    ax.set_ylim(0, peak_thousands * 1.16)

    # In date units now, so the annotation offset is in days rather than bars.
    peak = mdates.date2num(df.loc[df["revenue_brl"].idxmax(), "month"])
    ax.annotate(
        s["black_friday"],
        xy=(peak, peak_thousands),
        xytext=(peak - 75, peak_thousands * 1.05),
        ha="center",
        color=ACCENT,
        fontsize=9,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": ACCENT, "lw": 1.3, "shrinkA": 2},
    )
    ax.text(
        0.01,
        0.98,
        s["revenue_note"].format(orders=excluded_orders),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color=SOFT,
    )
    save(fig, lang, "revenue-monthly.png")


def chart_top_categories(data, s, lang: str) -> None:
    """The categories that carry the revenue."""
    df = data["categories"].iloc[::-1]

    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    ax.barh(df["category"], df["revenue_brl"] / 1_000, color=PRIMARY, height=0.68)
    ax.set_xlabel(s["categories_x"])
    ax.set_title(s["categories_title"])
    ax.grid(axis="y", visible=False)

    for y, (value, price) in enumerate(
        zip(df["revenue_brl"], df["avg_item_price_brl"], strict=True)
    ):
        ax.text(
            value / 1_000 + 12,
            y,
            s["avg_item"].format(value=price),
            va="center",
            fontsize=8,
            color=SOFT,
        )
    ax.margins(x=0.22)
    save(fig, lang, "top-categories.png")


def chart_delivery_review(data, s, lang: str) -> None:
    """The strongest relationship in the dataset, in one picture."""
    df = data["delivery"]

    # The bucket names are precise but far too long to sit side by side as axis
    # labels, so they are wrapped for display. The colour keys off the real name,
    # not the label, and the label itself is translated.
    labels = [s["buckets"][b] for b in df["delivery_bucket"]]

    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    bars = ax.bar(
        labels,
        df["avg_review_score"],
        color=[PRIMARY if b == "on time" else ACCENT for b in df["delivery_bucket"]],
        width=0.62,
    )
    ax.set_ylabel(s["delivery_y"])
    ax.set_ylim(0, 5)
    ax.set_title(s["delivery_title"])
    ax.grid(axis="x", visible=False)

    for bar, score, bad in zip(
        bars, df["avg_review_score"], df["pct_review_score_le2"], strict=True
    ):
        centre = bar.get_x() + bar.get_width() / 2
        ax.text(
            centre,
            score + 0.12,
            f"{score:.2f}",
            ha="center",
            fontweight="bold",
            fontsize=9.5,
        )
        ax.text(
            centre,
            0.20,
            s["share_le2"].format(value=bad),
            ha="center",
            fontsize=7.5,
            color="white",
        )
    save(fig, lang, "delivery-review.png")


def chart_late_by_state(data, s, lang: str) -> None:
    """Lateness is geographic, and it is not a small difference."""
    df = data["states"]

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    colours = [PRIMARY if st == "SP" else ACCENT for st in df["customer_state"]]
    ax.barh(df["customer_state"], df["late_pct"], color=colours, height=0.68)
    ax.set_xlabel(s["state_x"])
    ax.set_title(s["state_title"])
    ax.grid(axis="y", visible=False)

    # Every bar carries its denominator, so a state with 1,100 deliveries cannot
    # be read as though it ranked against one with 40,000.
    for y, (pct, orders) in enumerate(zip(df["late_pct"], df["delivered_orders"], strict=True)):
        ax.text(
            pct + 0.18,
            y,
            s["state_label"].format(pct=pct, orders=orders),
            va="center",
            fontsize=8,
            color=SOFT,
        )
    ax.margins(x=0.22)
    save(fig, lang, "late-by-state.png")


def chart_cohort_retention(data, s, lang: str) -> None:
    """Retention does not decay from a high base — it starts low and stays there."""
    df = data["cohort"]

    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    ax.bar(df["month_offset"].astype(str), df["retention_pct"], color=PRIMARY, width=0.6)
    ax.set_xlabel(s["cohort_x"])
    ax.set_ylabel(s["cohort_y"])
    ax.set_title(s["cohort_title"])
    ax.grid(axis="x", visible=False)

    for x, pct in zip(df["month_offset"].astype(str), df["retention_pct"], strict=True):
        # Offset the label in points, not in data units: every value here is under
        # 1%, so a data-unit offset puts the text back on the bar's top edge and
        # reads as though it has been struck through.
        ax.annotate(
            f"{pct:.2f}",
            (x, pct),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=8,
            color=SOFT,
        )
    ax.margins(y=0.22)
    save(fig, lang, "cohort-retention.png")


def chart_repeat_purchase(data, s, lang: str) -> None:
    """The number that reframes the whole analysis."""
    df = data["repeat"].copy()
    df["bucket"] = df["frequency"].map(lambda n: str(n) if n <= 4 else "5+")
    grouped = df.groupby("bucket", sort=False)["customers"].sum()

    fig, ax = plt.subplots(figsize=(7.4, 3.7))
    bars = ax.bar(grouped.index, grouped.values, color=[ACCENT] + [PRIMARY] * (len(grouped) - 1))
    ax.set_yscale("log")
    ax.set_ylabel(s["repeat_y"])
    ax.set_xlabel(s["repeat_x"])
    ax.set_title(s["repeat_title"])
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
    save(fig, lang, "repeat-purchase.png")


def chart_order_status(data, s, lang: str) -> None:
    """What the revenue figure includes, so nobody has to assume."""
    df = data["status"].copy()
    df["revenue"] = df["revenue"].fillna(0)
    cancelled = df["order_status"].isin(["canceled", "unavailable"])

    fig, ax = plt.subplots(figsize=(7.8, 3.5))
    ax.barh(
        df["order_status"],
        df["revenue"] / 1_000,
        color=[ACCENT if is_cancelled else PRIMARY for is_cancelled in cancelled],
        height=0.68,
    )
    ax.set_xscale("log")
    ax.set_xlabel(s["status_x"])
    ax.set_title(s["status_title"])
    ax.grid(axis="y", visible=False)
    ax.text(
        0.99,
        0.97,
        s["status_note"],
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=SOFT,
    )
    save(fig, lang, "order-status.png")


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
    data = load_data(engine)
    print(f"writing charts to {FIGURES_DIR.relative_to(REPO_ROOT)}")
    for lang in LANGS:
        for chart in CHARTS:
            chart(data, STRINGS[lang], lang)
        print(f"done. {len(CHARTS)} charts ({lang}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
