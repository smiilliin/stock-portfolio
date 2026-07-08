import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from modules.simulate import (
    get_band_strategy,
    get_none_strategy,
    get_simulation_metrics,
    get_submissive_strategy,
)


def run_strategy_experiment(
    tickers,
    portfolio_ratio,
    start_date,
    end_date,
    monthly_investment,
):
    strategies = {
        "None": get_none_strategy(),
        "Submissive": get_submissive_strategy(),
        "Band 5%": get_band_strategy(ratio_threshold=0.05),
    }

    strategy_results = [
        (
            strategy_name,
            get_simulation_metrics(
                tickers=tickers,
                portfolio_ratio=portfolio_ratio,
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                monthly_investment=monthly_investment,
            ),
        )
        for strategy_name, strategy in strategies.items()
    ]

    strategy_metrics = [
        {"strategy_name": strategy_name, **(result[1])}
        for strategy_name, result in strategy_results
    ]
    strategy_histories = [
        {"strategy_name": strategy_name, "history": result[0]}
        for strategy_name, result in strategy_results
    ]
    every_month_date = strategy_results[0][1][2]

    summary_df = pd.DataFrame(strategy_metrics).set_index("strategy_name")
    summary_df = summary_df.round(
        {
            "total_return_pct": 2,
            "annualized_return_pct": 2,
            "annualized_volatility_pct": 2,
            "max_drawdown_pct": 2,
            "worst_1m_return_pct": 2,
            "worst_3m_return_pct": 2,
            "cagr_pct": 2,
            "sharpe_ratio": 3,
        }
    )

    return (strategy_histories, summary_df, every_month_date)


def visualize_strategy_histories(
    output_path,
    strategy_histories,
    every_month_date,
    monthly_investment,
    title="Strategy Comparison",
):
    fig, axes = plt.subplots(1, 2, figsize=(10, 6), constrained_layout=True)

    fig.suptitle(title, fontsize=16, fontweight="bold")

    for item in strategy_histories:
        name = item["strategy_name"]
        history = item["history"]

        total_balance = history.sum(axis=1)
        invested_total = monthly_investment * np.arange(1, len(total_balance) + 1)
        normalized_balance = total_balance / invested_total
        axes[0].plot(every_month_date, normalized_balance, label=name)

    axes[0].plot(
        every_month_date,
        np.ones(len(every_month_date)),
        label="Total Invested Capital",
        linestyle="--",
        color="gray",
    )

    axes[0].set_title("Portfolio Balance by Strategy")
    axes[0].set_xlabel("Date")
    axes[0].set_ylabel("Value / Invested Capital")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    for item in strategy_histories:
        name = item["strategy_name"]
        history = item["history"]

        total_balance = history[:, 2]
        invested_total = monthly_investment * np.arange(1, len(total_balance) + 1)
        normalized_balance = total_balance / invested_total
        axes[1].plot(every_month_date, normalized_balance, label=name)

    axes[1].plot(
        every_month_date,
        np.ones(len(every_month_date)),
        label="Total Invested Capital",
        linestyle="--",
        color="gray",
    )

    axes[1].set_title("Liquid Assets by Strategy")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Value / Invested Capital")
    axes[1].legend()
    axes[1].grid(alpha=0.25)

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Comparison chart saved to {output_path}")
