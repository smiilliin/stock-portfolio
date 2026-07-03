#!/usr/bin/env python
# coding: utf-8


import argparse

from financial_fetch import HistoricalDataRequest, fetch_historical_data
import pandas as pd
from pandas import DataFrame

import matplotlib.pyplot as plt
import numpy as np

import dataframe_image as dfi

every_month_investment = 300


class Wallet:
    stocks: np.array[float]
    stocks_data: np.array[np.array[float]]

    def __init__(self, stocks_data: DataFrame):
        close_frame = pd.concat(
            [
                data["Close"].rename(f"stock_{index}")
                for index, data in enumerate(stocks_data)
            ],
            axis=1,
            join="outer",
            sort=False,
        ).sort_index()
        close_frame = close_frame.ffill().bfill()

        self.stocks = np.zeros(close_frame.shape[1])
        self.stocks_data = close_frame.to_numpy().T

    def invest(self, stock_index, date_index, amount):
        delta_stock_amount = amount / self.stocks_data[stock_index][date_index]
        self.stocks[stock_index] += delta_stock_amount

        return delta_stock_amount

    def invest_all_stocks(self, date_index, amount, ratio=(0.3, 0.1, 0.1)):
        ratio = np.array(ratio)
        ratio = ratio / sum(ratio)

        for stock_index in range(len(self.stocks)):
            self.invest(
                stock_index=stock_index,
                date_index=date_index,
                amount=amount * ratio[stock_index],
            )

    def get_balance(self, date_index):
        return np.array(
            [
                stock * self.stocks_data[stock_index][date_index]
                for stock_index, stock in enumerate(self.stocks)
            ]
        )

    def get_close_data(self, date_index):
        return np.array(
            [
                self.stocks_data[stock_index][date_index]
                for stock_index in range(len(self.stocks_data))
            ]
        )

    def rebalance(
        self,
        date_index,
        target_ratio=(0.3, 0.1, 0.1),
        strategy=lambda balance, portfolio_balance, current_ratio, target_ratio: portfolio_balance,
    ):
        portfolio_value = rebalance_portfolio(
            balance=self.get_balance(date_index),
            target_ratio=target_ratio,
            strategy=strategy,
        )
        self.stocks = portfolio_value / self.get_close_data(date_index)

        return portfolio_value


def rebalance_portfolio(balance, target_ratio, strategy: callable):
    target_ratio = np.array(target_ratio, dtype=float)
    target_ratio = target_ratio / sum(target_ratio)

    balance = np.array(balance, dtype=float)
    total = balance.sum()
    portfolio_balance = total * target_ratio
    current_ratio = balance / total

    return strategy(balance, portfolio_balance, current_ratio, target_ratio)


def none_strategy(balance, portfolio_balance, current_ratio, target_ratio):
    return balance


def submissive_strategy(balance, portfolio_balance, current_ratio, target_ratio):
    return portfolio_balance


def five_percent_strategy(
    balance, portfolio_balance, current_ratio, target_ratio, ratio_threshold=0.05
):
    ratio_filter = np.abs(current_ratio - target_ratio) > ratio_threshold

    if not np.any(ratio_filter):
        return balance

    return portfolio_balance


def run_wallet_simulation(
    wallet,
    every_month_date,
    every_month_investment,
    strategy: callable,
    portfolio_ratio=(0.3, 0.1, 0.1),
):
    wallet_history = []

    for date_index in range(len(every_month_date)):
        wallet.invest_all_stocks(date_index=date_index, amount=every_month_investment)

        wallet.rebalance(
            date_index=date_index,
            target_ratio=portfolio_ratio,
            strategy=strategy,
        )
        wallet_history.append(wallet.get_balance(date_index))

    return np.array(wallet_history)


def calculate_portfolio_metrics(
    portfolio_history: np.ndarray, periods_per_year: int = 12
):
    portfolio_value = np.asarray(portfolio_history, dtype=float).sum(axis=1)
    portfolio_series = pd.Series(portfolio_value)
    period_returns = portfolio_series.pct_change().dropna()
    drawdown = portfolio_series / portfolio_series.cummax() - 1
    worst_3m_return = portfolio_series.pct_change(3).dropna()

    total_return = portfolio_series.iloc[-1] / portfolio_series.iloc[0] - 1
    annualized_return = (1 + total_return) ** (
        periods_per_year / max(len(portfolio_series) - 1, 1)
    ) - 1
    annualized_volatility = (
        period_returns.std() * np.sqrt(periods_per_year)
        if not period_returns.empty
        else 0.0
    )
    max_drawdown = drawdown.min() if not drawdown.empty else 0.0
    worst_1m_return = period_returns.min() if not period_returns.empty else 0.0
    worst_3m_return_value = worst_3m_return.min() if not worst_3m_return.empty else 0.0
    sharpe_ratio = (
        annualized_return / annualized_volatility if annualized_volatility else np.nan
    )

    return {
        "total_return_pct": total_return * 100,
        "annualized_return_pct": annualized_return * 100,
        "annualized_volatility_pct": annualized_volatility * 100,
        "max_drawdown_pct": max_drawdown * 100,
        "worst_1m_return_pct": worst_1m_return * 100,
        "worst_3m_return_pct": worst_3m_return_value * 100,
        "sharpe_ratio": sharpe_ratio,
    }


def parse_csv_values(raw_value: str, cast_type):
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    return [cast_type(value) for value in values]


def build_output_name(base_name: str, suffix: str, extension: str):
    safe_suffix = suffix.strip().replace(" ", "_")
    if not safe_suffix:
        return f"{base_name}.{extension}"

    return f"{base_name}_{safe_suffix}.{extension}"


def fetch_stock_data(tickers, start_date, end_date):
    return [
        fetch_historical_data(
            HistoricalDataRequest(
                ticker=ticker,
                start=start_date,
                end=end_date,
                interval="1mo",
            )
        )
        for ticker in tickers
    ]


def run_portfolio_experiment(
    tickers,
    portfolio_ratio,
    output_suffix="",
    start_date="2000-01-01",
    end_date="2026-01-02",
    monthly_investment=every_month_investment,
):
    stock_data = fetch_stock_data(tickers, start_date, end_date)
    every_month_date = pd.to_datetime(stock_data[0].index)

    strategy_histories = {
        "None": run_wallet_simulation(
            wallet=Wallet(stocks_data=stock_data),
            every_month_date=every_month_date,
            every_month_investment=monthly_investment,
            strategy=none_strategy,
            portfolio_ratio=portfolio_ratio,
        ),
        "Submissive": run_wallet_simulation(
            wallet=Wallet(stocks_data=stock_data),
            every_month_date=every_month_date,
            every_month_investment=monthly_investment,
            strategy=submissive_strategy,
            portfolio_ratio=portfolio_ratio,
        ),
        "Five Percent": run_wallet_simulation(
            wallet=Wallet(stocks_data=stock_data),
            every_month_date=every_month_date,
            every_month_investment=monthly_investment,
            strategy=five_percent_strategy,
            portfolio_ratio=portfolio_ratio,
        ),
    }

    from IPython.display import display

    summary_rows = []

    for strategy_name, history in strategy_histories.items():
        metrics = calculate_portfolio_metrics(history)
        summary_rows.append({"strategy": strategy_name, **metrics})

    summary_df = pd.DataFrame(summary_rows)
    rounded_summary_df = summary_df.round(
        {
            "total_return_pct": 2,
            "annualized_return_pct": 2,
            "annualized_volatility_pct": 2,
            "max_drawdown_pct": 2,
            "worst_1m_return_pct": 2,
            "worst_3m_return_pct": 2,
            "sharpe_ratio": 3,
        }
    )
    display(rounded_summary_df)

    summary_output_path_json = build_output_name(
        "strategy_summary", output_suffix, "json"
    )
    summary_output_path_png = build_output_name(
        "strategy_summary", output_suffix, "png"
    )
    summary_df.to_json(summary_output_path_json, index=False)
    dfi.export(summary_df, summary_output_path_png, table_conversion="matplotlib")

    fig, axes = plt.subplots(1, 2, figsize=(10, 6), constrained_layout=True)

    for strategy_name, history in strategy_histories.items():
        total_balance = history.sum(axis=1)
        invested_total = monthly_investment * np.arange(1, len(total_balance) + 1)
        normalized_balance = total_balance / invested_total
        axes[0].plot(every_month_date, normalized_balance, label=strategy_name)

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

    for strategy_name, history in strategy_histories.items():
        total_balance = history[:, 2]
        invested_total = monthly_investment * np.arange(1, len(total_balance) + 1)
        normalized_balance = total_balance / invested_total
        axes[1].plot(every_month_date, normalized_balance, label=strategy_name)

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

    output_path = build_output_name("strategy_comparison", output_suffix, "png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved summary to {summary_output_path_json}, {summary_output_path_png}")
    print(f"Saved comparison chart to {output_path}")


def build_argument_parser():
    parser = argparse.ArgumentParser(description="Run stock portfolio simulations.")
    parser.add_argument(
        "--tickers",
        default="VOO,VXUS,TLT",
        help="Comma-separated tickers to compare, for example VOO,VXUS,TLT",
    )
    parser.add_argument(
        "--portfolio-ratio",
        default="0.3,0.1,0.1",
        help="Comma-separated target ratios that match --tickers",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="Suffix to append to saved files, for example core or test01",
    )
    parser.add_argument(
        "--start-date",
        default="2000-01-01",
        help="Historical data start date",
    )
    parser.add_argument(
        "--end-date",
        default="2026-01-02",
        help="Historical data end date",
    )
    parser.add_argument(
        "--monthly-investment",
        type=float,
        default=every_month_investment,
        help="Amount invested each month",
    )
    return parser


def main():
    args = build_argument_parser().parse_args()
    tickers = parse_csv_values(args.tickers, str)
    portfolio_ratio = parse_csv_values(args.portfolio_ratio, float)

    if len(tickers) != len(portfolio_ratio):
        raise ValueError("--tickers and --portfolio-ratio must have the same length")

    run_portfolio_experiment(
        tickers=tickers,
        portfolio_ratio=portfolio_ratio,
        output_suffix=args.output_suffix,
        start_date=args.start_date,
        end_date=args.end_date,
        monthly_investment=args.monthly_investment,
    )


if __name__ == "__main__":
    main()
