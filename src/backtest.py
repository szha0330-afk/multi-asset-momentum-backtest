import os
import pandas as pd
import matplotlib.pyplot as plt

from config import (
    TICKERS,
    BENCHMARK,
    START_DATE,
    END_DATE,
    MOMENTUM_WINDOW,
    TOP_N,
    RESULTS_DIR
)
from data_loader import load_price_data
from signals import generate_momentum_weights
from portfolio import calculate_portfolio_returns, calculate_benchmark_returns
from metrics import calculate_performance_metrics, calculate_drawdown


def run_backtest():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("Downloading price data...")
    prices = load_price_data(TICKERS, START_DATE, END_DATE)

    print("Generating momentum portfolio weights...")
    weights = generate_momentum_weights(
        prices,
        window=MOMENTUM_WINDOW,
        top_n=TOP_N
    )

    print("Running portfolio backtest...")
    portfolio_result = calculate_portfolio_returns(prices, weights)
    benchmark_result = calculate_benchmark_returns(prices, BENCHMARK)

    combined = pd.concat(
        [
            portfolio_result,
            benchmark_result
        ],
        axis=1
    )

    portfolio_metrics = calculate_performance_metrics(
        combined["portfolio_return"],
        combined["equity_curve"]
    )

    benchmark_metrics = calculate_performance_metrics(
        combined["benchmark_return"],
        combined["benchmark_equity"]
    )

    performance_report = pd.DataFrame({
        "Momentum Portfolio": portfolio_metrics,
        "Benchmark": benchmark_metrics
    })

    weights.to_csv(f"{RESULTS_DIR}/weights.csv")
    combined.to_csv(f"{RESULTS_DIR}/backtest_results.csv")
    performance_report.to_csv(f"{RESULTS_DIR}/performance_report.csv")

    plt.figure(figsize=(10, 6))
    plt.plot(combined.index, combined["equity_curve"], label="Momentum Portfolio")
    plt.plot(combined.index, combined["benchmark_equity"], label=f"{BENCHMARK} Buy and Hold")
    plt.title("Momentum Portfolio vs Benchmark")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.legend()
    plt.savefig(f"{RESULTS_DIR}/equity_curve.png")
    plt.close()

    portfolio_drawdown = calculate_drawdown(combined["equity_curve"])
    benchmark_drawdown = calculate_drawdown(combined["benchmark_equity"])

    plt.figure(figsize=(10, 6))
    plt.plot(portfolio_drawdown.index, portfolio_drawdown, label="Momentum Portfolio Drawdown")
    plt.plot(benchmark_drawdown.index, benchmark_drawdown, label=f"{BENCHMARK} Drawdown")
    plt.title("Drawdown Comparison")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.savefig(f"{RESULTS_DIR}/drawdown.png")
    plt.close()

    print("\nBacktest Completed")
    print("------------------")
    print(performance_report)


if __name__ == "__main__":
    run_backtest()