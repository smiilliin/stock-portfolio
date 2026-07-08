import numpy as np
import pandas as pd

type Strategy = callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]


def get_none_strategy() -> Strategy:
    return lambda balance, portfolio_balance, current_ratio, target_ratio: balance


def get_submissive_strategy() -> Strategy:
    return (
        lambda balance, portfolio_balance, current_ratio, target_ratio: portfolio_balance
    )


def get_band_strategy(ratio_threshold=0.05) -> Strategy:
    def band_strategy(balance, portfolio_balance, current_ratio, target_ratio):
        return band_strategy_impl(
            balance, portfolio_balance, current_ratio, target_ratio, ratio_threshold
        )

    return band_strategy


def band_strategy_impl(
    balance, portfolio_balance, current_ratio, target_ratio, ratio_threshold=0.05
):
    ratio_filter = np.abs(current_ratio - target_ratio) > ratio_threshold

    if not np.any(ratio_filter):
        return balance

    return portfolio_balance


from modules.financial_fetch import fetch_stock_data
from modules.wallet import Wallet


def run_wallet_simulation(
    wallet: Wallet,
    every_month_date,
    every_month_investment,
    strategy: Strategy,
    portfolio_ratio,
):
    wallet_history = []

    for date_index in range(len(every_month_date)):
        wallet.invest_all_stocks(
            date_index=date_index, amount=every_month_investment, ratio=portfolio_ratio
        )

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
    volatility = (
        period_returns.std() * np.sqrt(periods_per_year)
        if not period_returns.empty
        else 0.0
    )
    mdd = drawdown.min() if not drawdown.empty else 0.0
    worst_1m = period_returns.min() if not period_returns.empty else 0.0
    worst_3m = worst_3m_return.min() if not worst_3m_return.empty else 0.0
    sharpe = annualized_return / volatility if volatility else np.nan
    cagr = (portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (
        1 / (len(portfolio_series) / periods_per_year)
    ) - 1
    final_value = portfolio_series.iloc[-1] if not portfolio_series.empty else 0.0

    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "volatility": volatility,
        "mdd": mdd,
        "worst_1m": worst_1m,
        "worst_3m": worst_3m,
        "final_value": final_value,
    }


def get_simulation_metrics(
    tickers,
    portfolio_ratio,
    strategy,
    monthly_investment,
    start_date=None,
    end_date=None,
    stock_data=None,
):
    if stock_data is None:
        stock_data = fetch_stock_data(tickers, start_date, end_date)

    every_month_date = pd.to_datetime(stock_data[0].index)

    wallet = Wallet(stocks_data=stock_data)
    wallet_history = run_wallet_simulation(
        wallet=wallet,
        every_month_date=every_month_date,
        every_month_investment=monthly_investment,
        strategy=strategy,
        portfolio_ratio=portfolio_ratio,
    )

    metrics = calculate_portfolio_metrics(wallet_history)

    return wallet_history, metrics, every_month_date
