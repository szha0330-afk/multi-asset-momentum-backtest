# Multi-Asset Momentum Backtest

A Python backtesting project for a multi-asset momentum portfolio strategy.

## Project Overview

This project builds a multi-asset momentum portfolio backtesting system.

The strategy selects the strongest assets based on past momentum and rebalances the portfolio monthly.

## Asset Universe

The strategy uses the following ETFs:

- SPY: S&P 500 ETF
- QQQ: Nasdaq 100 ETF
- IWM: Russell 2000 ETF
- TLT: Long-Term Treasury ETF
- GLD: Gold ETF

## Strategy Logic

The strategy follows these steps:

1. Download historical ETF price data
2. Calculate 126-day momentum for each asset
3. Rank assets by momentum
4. Select the top 2 assets
5. Allocate equal weight to selected assets
6. Rebalance monthly
7. Apply transaction costs
8. Compare performance against SPY buy-and-hold

## Tools Used

- Python
- pandas
- numpy
- matplotlib
- yfinance

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt