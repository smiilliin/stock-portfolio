import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from modules.financial_fetch import fetch_stock_data
from modules.simulate import get_band_strategy, get_simulation_metrics


def normalize(series, higher_is_better=True):
    if higher_is_better:
        return (series - series.min()) / (series.max() - series.min())

    return (series.max() - series) / (series.max() - series.min())


def generate_ratios(n, step=0.1):
    values = np.arange(0, 1 + step, step)

    def dfs(depth, remain, current):
        # 남은 비율을 그대로 사용
        if depth == n - 1:
            yield current + [round(remain, 10)]
            return

        for v in values:
            if v > remain:
                break

            yield from dfs(depth + 1, round(remain - v, 10), current + [v])

    yield from dfs(0, 1.0, [])


def calculate_score(df, score_weights=None):
    cagr_norm = normalize(df["cagr"])
    sharpe_norm = normalize(df["sharpe"])
    mdd_norm = normalize(df["mdd"], False)
    volatility_norm = normalize(df["volatility"], False)

    if score_weights is None:
        score_weights = [0.35, 0.25, 0.25, 0.15]

    cagr_norm *= score_weights[0]
    sharpe_norm *= score_weights[1]
    volatility_norm *= -score_weights[2]
    mdd_norm *= -score_weights[3]

    return cagr_norm + sharpe_norm + mdd_norm + volatility_norm


def highlight_ranking(df, df_frontier=None, no_score_column=False):
    COLORS = [
        "#FFD700",  # 🥇
        "#C0C0C0",  # 🥈
        "#CD7F32",  # 🥉
    ]

    FRONTIER_COLOR = "background-color: #B0E0E6;"

    CRITERIA = {
        "score": "max",
        "cagr": "max",
        "sharpe": "max",
        "volatility": "min",
        "mdd": "max",
        "worst_1m": "max",
        "worst_3m": "max",
        "final_value": "max",
    }

    style = pd.DataFrame("", index=df.index, columns=df.columns)

    # Frontier 먼저 표시
    if df_frontier is not None:
        style.loc[df_frontier.index, "ratio"] = FRONTIER_COLOR

    # 각 지표 Top3 표시
    for col, method in CRITERIA.items():
        if no_score_column and col == "score":
            continue

        ranking = (
            df[col].nlargest(3).index if method == "max" else df[col].nsmallest(3).index
        )

        for color, idx in zip(COLORS, ranking):
            style.loc[idx, col] = f"background-color: {color};"

    return style


def run_ratio_experiment(
    tickers,
    start_date,
    end_date,
    monthly_investment,
    score_weights=None,
    no_zero_ratio=False,
    step=0.1,
    percent=False,
):
    stock_data = fetch_stock_data(tickers, start_date, end_date)
    strategy = get_band_strategy(ratio_threshold=0.05)

    results = []
    for portfolio_ratio in generate_ratios(len(tickers), step=step):
        if no_zero_ratio and any(r == 0 for r in portfolio_ratio):
            continue

        metrics = get_simulation_metrics(
            tickers=tickers,
            portfolio_ratio=portfolio_ratio,
            strategy=strategy,
            monthly_investment=monthly_investment,
            start_date=start_date,
            end_date=end_date,
            stock_data=stock_data,
        )[1]

        if not percent:
            metrics["ratio"] = ",".join([f"{x:.1f}" for x in portfolio_ratio])
        else:
            metrics["ratio"] = ",".join([f"{x * 100:.1f}%" for x in portfolio_ratio])
        results.append(metrics)

    df = pd.DataFrame(results)

    frontier_indicies = []
    for idx, p in df.iterrows():
        dominated = False
        for q in results:
            if (
                q["cagr"] >= p["cagr"]
                and q["volatility"] <= p["volatility"]
                and (q["cagr"] > p["cagr"] or q["volatility"] < p["volatility"])
            ):
                dominated = True
                break

        if not dominated:
            frontier_indicies.append(idx)

    score = calculate_score(df, score_weights=score_weights)

    # 컬럼 순서 바꾸기
    ratio = df.pop("ratio")
    df.insert(0, "ratio", ratio)

    df.insert(1, "score", score)
    df.sort_values(by="score", ascending=False, inplace=True)

    df_frontier = df.loc[frontier_indicies]

    return df, df_frontier


def visualize_ratio_result(
    df,
    df_frontier,
    output_path,
    title="Portfolio Ratio Experiment",
):
    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)

    ax.set_title(title)
    ax.set_xlabel("Volatility")
    ax.set_ylabel("CAGR")
    ax.grid(alpha=0.5)

    scatter = ax.scatter(
        df["volatility"],
        df["cagr"],
        c=df["score"],
        cmap="viridis",
        s=30 + (-df["mdd"]) * 300,
        alpha=0.8,
        edgecolors="black",
        linewidths=0.3,
    )

    df_frontier = df_frontier.sort_values("volatility")
    ax.plot(
        df_frontier["volatility"],
        df_frontier["cagr"],
        c="red",
        alpha=0.9,
        label="Efficient Frontier",
    )
    ax.scatter(
        df_frontier["volatility"],
        df_frontier["cagr"],
        facecolors="none",
        edgecolors="red",
        linewidth=2,
        s=30 + (-df_frontier["mdd"]) * 300,
    )
    best = df.loc[df["score"].idxmax()]

    ax.scatter(
        best["volatility"],
        best["cagr"],
        marker="*",
        s=350,
        color="gold",
        edgecolors="black",
    )
    for _, row in df_frontier.iterrows():
        ax.annotate(
            row["ratio"],
            (row["volatility"], row["cagr"]),
            fontsize=10,
            fontweight="bold",
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
        )

    fig.colorbar(scatter, ax=ax, label="Score")

    fig.savefig(output_path, dpi=300)
    print(f"Result graph saved to {output_path}")
