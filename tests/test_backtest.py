"""Regression tests for the multi-asset momentum strategy."""

import sys
import unittest
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio import calculate_portfolio_returns  # noqa: E402
from signals import generate_momentum_weights  # noqa: E402
from metrics import calculate_drawdown  # noqa: E402


class MomentumWeightsTests(unittest.TestCase):
    def test_rotation_does_not_keep_sold_assets(self):
        dates = pd.to_datetime(
            ["2024-01-30", "2024-01-31", "2024-02-27", "2024-02-28"]
        )
        prices = pd.DataFrame(
            [[100, 100, 100], [110, 105, 90], [100, 100, 100], [90, 102, 120]],
            index=dates, columns=["A", "B", "C"]
        )
        weights = generate_momentum_weights(prices, window=1, top_n=2)

        self.assertEqual(weights.loc["2024-01-30"].sum(), 0.0)
        self.assertEqual(weights.loc["2024-01-31", "A"], 0.5)
        self.assertEqual(weights.loc["2024-02-27", "A"], 0.5)
        self.assertEqual(weights.loc["2024-02-28", "A"], 0.0)
        self.assertEqual(weights.loc["2024-02-28", "C"], 0.5)
        self.assertTrue(weights.sum(axis=1).le(1.0 + 1e-10).all())
        self.assertTrue(weights.gt(0).sum(axis=1).le(2).all())

    def test_insufficient_history_remains_in_cash(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        prices = pd.DataFrame({"A": [100, 101, 102], "B": [100, 99, 98]}, index=dates)
        weights = generate_momentum_weights(prices, window=5, top_n=2)
        self.assertTrue(weights.eq(0.0).all().all())

    def test_bad_top_n_is_rejected(self):
        prices = pd.DataFrame({"A": [100, 110]}, index=pd.date_range("2024-01-01", periods=2))
        with self.assertRaises(ValueError):
            generate_momentum_weights(prices, window=1, top_n=2)


class PortfolioExecutionTests(unittest.TestCase):
    def setUp(self):
        dates = pd.to_datetime(
            ["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02", "2024-02-28"]
        )
        self.prices = pd.DataFrame(
            {"A": [100, 100, 110, 121, 121], "B": [100, 100, 100, 100, 100]},
            index=dates
        )
        self.weights = pd.DataFrame(
            {"A": [0, .5, .5, .5, .5], "B": [0, .5, .5, .5, .5]},
            index=dates
        )

    def test_no_same_day_signal_return_and_monthly_drift(self):
        result = calculate_portfolio_returns(self.prices, self.weights, transaction_cost=.001)
        self.assertAlmostEqual(result.loc["2024-01-31", "gross_return"], 0.0)
        self.assertAlmostEqual(result.loc["2024-01-31", "transaction_cost"], .001)
        self.assertAlmostEqual(result.loc["2024-02-01", "gross_return"], .05)
        self.assertGreater(result.loc["2024-02-02", "gross_return"], .05)
        self.assertEqual(result.loc["2024-02-02", "turnover"], 0.0)
        self.assertGreater(result.loc["2024-02-28", "turnover"], 0.0)
        self.assertGreater(result.loc["2024-02-28", "transaction_cost"], 0.0)
        self.assertTrue(result["equity_curve"].gt(0).all())

    def test_leveraged_targets_are_rejected(self):
        bad_weights = self.weights.copy()
        bad_weights.loc["2024-01-31", "A"] = 1.0
        with self.assertRaisesRegex(ValueError, "leverage"):
            calculate_portfolio_returns(self.prices, bad_weights)

    def test_initial_trading_cost_counts_as_drawdown(self):
        curve = pd.Series([0.999, 1.001, 0.998])
        drawdown = calculate_drawdown(curve)
        self.assertAlmostEqual(drawdown.iloc[0], -0.001)


if __name__ == "__main__":
    unittest.main()
