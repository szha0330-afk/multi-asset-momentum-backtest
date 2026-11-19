import numpy as np
import pandas as pd

from config import TRANSACTION_COST, BENCHMARK
from signals import get_month_end_trading_dates


def calculate_portfolio_returns(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    transaction_cost: float = TRANSACTION_COST
) -> pd.DataFrame:
    """Monthly buy-and-hold with drift and close-of-day rebalancing.

    The target is formed from that day's closing prices and only affects
    subsequent daily price returns. Trading costs are deducted at rebalance
    close, based on the difference from the actual drifted allocation.
    """
    if transaction_cost < 0:
        raise ValueError("transaction_cost must be non-negative")
    if not prices.index.equals(weights.index) or not prices.columns.equals(weights.columns):
        raise ValueError("prices and weights must have identical index and columns")
    if not np.isfinite(weights.to_numpy(dtype=float)).all():
        raise ValueError("weights must be finite")
    if (weights < -1e-10).any().any() or (weights.sum(axis=1) > 1 + 1e-10).any():
        raise ValueError("target weights must be long-only with leverage <= 1")

    asset_returns = prices.pct_change(fill_method=None).fillna(0.0)
    rebalance_dates = set(get_month_end_trading_dates(prices))
    held_weights = np.zeros(len(prices.columns), dtype=float)
    rows = []

    for date, daily_returns in asset_returns.iterrows():
        daily = daily_returns.to_numpy(dtype=float)
        gross_return = float(held_weights @ daily)
        if 1 + gross_return <= 0:
            raise ValueError("portfolio equity was exhausted")

        # Without trading, winners grow in weight and losers shrink.
        drifted_weights = held_weights * (1 + daily) / (1 + gross_return)
        turnover = 0.0
        cost = 0.0

        if date in rebalance_dates:
            target = weights.loc[date].to_numpy(dtype=float)
            turnover = float(np.abs(target - drifted_weights).sum())
            cost = (1 + gross_return) * turnover * transaction_cost
            held_weights = target
        else:
            held_weights = drifted_weights

        rows.append((gross_return, cost, gross_return - cost, turnover))

    result = pd.DataFrame(
        rows, index=prices.index,
        columns=["gross_return", "transaction_cost", "portfolio_return", "turnover"]
    )
    result["equity_curve"] = (1 + result["portfolio_return"]).cumprod()

    return result


def calculate_benchmark_returns(
    prices: pd.DataFrame,
    benchmark: str = BENCHMARK
) -> pd.DataFrame:
    benchmark_returns = prices[benchmark].pct_change(fill_method=None).fillna(0)
    benchmark_equity = (1 + benchmark_returns).cumprod()

    result = pd.DataFrame(index=prices.index)
    result["benchmark_return"] = benchmark_returns
    result["benchmark_equity"] = benchmark_equity

    return result
