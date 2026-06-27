#!/usr/bin/env python
# coding: utf-8


from financial_fetch import HistoricalDataRequest, fetch_historical_data
import pandas as pd
from pandas import DataFrame

import matplotlib.pyplot as plt
import numpy as np

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
    wallet, every_month_date, every_month_investment, strategy: callable
):
    wallet_history = []

    for date_index in range(len(every_month_date)):
        wallet.invest_all_stocks(date_index=date_index, amount=every_month_investment)

        wallet.rebalance(
            date_index=date_index,
            target_ratio=(0.3, 0.1, 0.1),
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


start_date = "2000-01-01"
end_date = "2026-01-02"

voo_data = fetch_historical_data(
    HistoricalDataRequest(ticker="VOO", start=start_date, end=end_date, interval="1mo")
)
vxus_data = fetch_historical_data(
    HistoricalDataRequest(ticker="VXUS", start=start_date, end=end_date, interval="1mo")
)
sgov_data = fetch_historical_data(
    HistoricalDataRequest(ticker="SGOV", start=start_date, end=end_date, interval="1mo")
)
every_month_date = pd.to_datetime(voo_data.index)


none_history = run_wallet_simulation(
    wallet=Wallet(stocks_data=[voo_data, vxus_data, sgov_data]),
    every_month_date=every_month_date,
    every_month_investment=every_month_investment,
    strategy=none_strategy,
)
submissive_history = run_wallet_simulation(
    wallet=Wallet(stocks_data=[voo_data, vxus_data, sgov_data]),
    every_month_date=every_month_date,
    every_month_investment=every_month_investment,
    strategy=submissive_strategy,
)
five_percent_history = run_wallet_simulation(
    wallet=Wallet(stocks_data=[voo_data, vxus_data, sgov_data]),
    every_month_date=every_month_date,
    every_month_investment=every_month_investment,
    strategy=five_percent_strategy,
)


from IPython.display import display

strategy_histories = {
    "None": none_history,
    "Submissive": submissive_history,
    "Five Percent": five_percent_history,
}

summary_rows = []
monthly_dates = pd.to_datetime(every_month_date)

for strategy_name, history in strategy_histories.items():
    metrics = calculate_portfolio_metrics(history)

    summary_rows.append(
        {
            "strategy": strategy_name,
            **metrics,
        }
    )

summary_df = pd.DataFrame(summary_rows)
display(
    summary_df.round(
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
)

fig, axes = plt.subplots(1, 2, figsize=(10, 6), constrained_layout=True)

for strategy_name, history in strategy_histories.items():
    total_balance = history.sum(axis=1)
    invested_total = every_month_investment * np.arange(1, len(total_balance) + 1)
    normalized_balance = total_balance / invested_total
    axes[0].plot(monthly_dates, normalized_balance, label=strategy_name)


axes[0].plot(
    monthly_dates,
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
    invested_total = every_month_investment * np.arange(1, len(total_balance) + 1)
    normalized_balance = total_balance / invested_total
    axes[1].plot(monthly_dates, normalized_balance, label=strategy_name)


axes[1].plot(
    monthly_dates,
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


output_path = "strategy_comparison.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Saved comparison chart to {output_path}")
