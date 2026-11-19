import pandas as pd
import numpy as np

from config import MOMENTUM_WINDOW, TOP_N


def calculate_momentum(
    prices: pd.DataFrame,
    window: int = MOMENTUM_WINDOW
) -> pd.DataFrame:
    momentum = prices / prices.shift(window) - 1
    return momentum


def get_month_end_trading_dates(prices: pd.DataFrame) -> pd.DatetimeIndex:
    month_end_dates = prices.groupby(
        [prices.index.year, prices.index.month]
    ).tail(1).index

    return month_end_dates


def generate_momentum_weights(
    prices: pd.DataFrame,
    window: int = MOMENTUM_WINDOW,
    top_n: int = TOP_N
) -> pd.DataFrame:
    """Target close-of-day weights, updated at each month's final trading day.

    Entire portfolio rows are carried forward between rebalances. In
    particular, a zero target weight must remain zero for a sold asset.
    """
    if window < 1:
        raise ValueError("window must be at least one trading day")
    if not 1 <= top_n <= len(prices.columns):
        raise ValueError("top_n must be between 1 and the asset count")
    if prices.empty:
        raise ValueError("prices must not be empty")

    momentum = calculate_momentum(prices, window)
    rebalance_dates = get_month_end_trading_dates(prices)

    rebalance_weights = pd.DataFrame(
        index=rebalance_dates, columns=prices.columns, dtype=float
    )

    for date in rebalance_dates:
        scores = momentum.loc[date].replace([np.inf, -np.inf], np.nan).dropna()

        if len(scores) < top_n:
            continue

        selected_assets = scores.nlargest(top_n).index
        rebalance_weights.loc[date] = 0.0
        rebalance_weights.loc[date, selected_assets] = 1 / top_n

    return rebalance_weights.reindex(prices.index).ffill().fillna(0.0)
