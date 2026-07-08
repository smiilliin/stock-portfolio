import matplotlib.pyplot as plt
import pandas as pd

from experiments.ratio import calculate_score, generate_ratios
from modules.financial_fetch import fetch_stock_data
from modules.simulate import get_band_strategy, get_simulation_metrics


def run_ratio2_experiment(
    tickers,
    start_date,
    end_date,
    monthly_investment,
    score_weights=None,
    no_zero_ratio=False,
    step=0.1,
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

        results.append(
            {
                **metrics,
                **{ticker: ratio for ticker, ratio in zip(tickers, portfolio_ratio)},
            }
        )

    df = pd.DataFrame(results)

    score = calculate_score(df, score_weights=score_weights)

    df.insert(1, "score", score)
    df.sort_values(by="score", ascending=False, inplace=True)

    return df


def save_heatmap(heat, output_path):
    fig, ax = plt.subplots(figsize=(8, 6))

    im = ax.imshow(
        heat,
        origin="lower",
        aspect="auto",
        cmap="viridis",
    )

    ax.set_xticks(range(len(heat.columns)))
    ax.set_xticklabels([f"{x:.0%}" for x in heat.columns])

    ax.set_yticks(range(len(heat.index)))
    ax.set_yticklabels([f"{y:.0%}" for y in heat.index])

    ax.set_xlabel("VOO")
    ax.set_ylabel("SCHD")

    fig.colorbar(im, ax=ax, label="Score")

    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):

            value = heat.iat[i, j]

            if pd.notna(value):
                ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if value < heat.values.mean() else "black",
                )

    # fig.colorbar(, ax=ax, label="Score")

    fig.savefig(output_path, dpi=300)
    print(f"Result graph saved to {output_path}")


def visualize_ratio2_result(
    df,
    tickers,
    output_path,
    title="Portfolio Ratio Experiment",
):
    # if len(tickers) != 3:
    #     raise ValueError(
    #         "visualize_ratio2_result currently supports only 3 tickers for visualization."
    #     )

    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)

    # ax.set_title(title)
    # ax.set_xlabel("Volatility")
    # ax.set_ylabel("CAGR")
    # ax.grid(alpha=0.5)

    for vgit in sorted(df[tickers[2]].unique()):
        heat_df = df[df[tickers[2]] == vgit]

        heat_df = pd.DataFrame(heat_df, columns=[tickers[0], tickers[1], "score"])

        heat = heat_df.pivot(
            index=tickers[1],
            columns=tickers[0],
            values="score",
        )
        heat = heat.sort_index()
        heat = df[df[tickers[3]] == vgit].pivot(
            index=tickers[1],
            columns=tickers[0],
            values="score",
        )

        save_heatmap(heat, output_path + f"_VGIT_{vgit:.0%}.png")
