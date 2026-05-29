import pandas as pd

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
    momentum = calculate_momentum(prices, window)
    rebalance_dates = get_month_end_trading_dates(prices)

    weights = pd.DataFrame(
        0.0,
        index=prices.index,
        columns=prices.columns
    )

    for date in rebalance_dates:
        scores = momentum.loc[date].dropna()

        if len(scores) < top_n:
            continue

        selected_assets = scores.nlargest(top_n).index
        weights.loc[date, selected_assets] = 1 / top_n

    weights = weights.replace(0.0, pd.NA)
    weights = weights.ffill()
    weights = weights.fillna(0.0)

    return weights