import numpy as np
import pandas as pd
from pandas import DataFrame

from modules.simulate import Strategy, get_submissive_strategy


def rebalance_portfolio(balance, target_ratio, strategy: Strategy) -> np.ndarray:
    target_ratio = np.array(target_ratio, dtype=float)
    target_ratio = target_ratio / sum(target_ratio)

    balance = np.array(balance, dtype=float)
    total = balance.sum()
    portfolio_balance = total * target_ratio
    current_ratio = balance / total

    return strategy(balance, portfolio_balance, current_ratio, target_ratio)


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

    def invest_all_stocks(self, date_index, amount, ratio):
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
        target_ratio,
        strategy=None,
    ):
        if strategy is None:
            strategy = get_submissive_strategy()

        portfolio_value = rebalance_portfolio(
            balance=self.get_balance(date_index),
            target_ratio=target_ratio,
            strategy=strategy,
        )
        self.stocks = portfolio_value / self.get_close_data(date_index)

        return portfolio_value
