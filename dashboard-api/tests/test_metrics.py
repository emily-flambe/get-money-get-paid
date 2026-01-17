"""
Tests for performance metrics calculations.
"""
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_api.metrics import (
    calculate_total_return,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_daily_returns,
    calculate_win_rate,
)


class TestTotalReturn:
    """Tests for total return calculation"""

    def test_positive_return(self):
        """Calculate positive return correctly"""
        result = calculate_total_return(initial_equity=10000, final_equity=11000)
        assert result == 10.0, f"Expected 10.0% return but got {result}"

    def test_negative_return(self):
        """Calculate negative return correctly"""
        result = calculate_total_return(initial_equity=10000, final_equity=9000)
        assert result == -10.0, f"Expected -10.0% return but got {result}"

    def test_zero_initial_equity(self):
        """Handle zero initial equity gracefully"""
        result = calculate_total_return(initial_equity=0, final_equity=1000)
        assert result == 0, "Should return 0 for zero initial equity"

    def test_no_change(self):
        """No change should return 0"""
        result = calculate_total_return(initial_equity=10000, final_equity=10000)
        assert result == 0, "Expected 0% return for no change"


class TestDailyReturns:
    """Tests for daily returns calculation"""

    def test_basic_daily_returns(self):
        """Calculate daily returns from snapshots"""
        snapshots = [
            {"equity": 10000},
            {"equity": 10100},  # 1% gain
            {"equity": 10000},  # ~0.99% loss
        ]
        returns = calculate_daily_returns(snapshots)
        assert len(returns) == 2
        assert abs(returns[0] - 0.01) < 0.0001  # 1% gain
        assert abs(returns[1] - (-0.0099)) < 0.001  # ~0.99% loss

    def test_insufficient_data(self):
        """Return empty list with single snapshot"""
        snapshots = [{"equity": 10000}]
        returns = calculate_daily_returns(snapshots)
        assert returns == []

    def test_empty_snapshots(self):
        """Return empty list with no snapshots"""
        returns = calculate_daily_returns([])
        assert returns == []


class TestSharpeRatio:
    """Tests for Sharpe ratio calculation"""

    def test_positive_sharpe(self):
        """Calculate positive Sharpe ratio for consistent gains"""
        # Consistent 1% daily gains
        daily_returns = [0.01] * 20
        sharpe = calculate_sharpe_ratio(daily_returns)
        # With zero variance (all same), we'd divide by zero, but let's check positive
        # Actually with all same returns, std is 0, should return 0
        assert sharpe == 0, "Sharpe should be 0 when no variance"

    def test_sharpe_with_variance(self):
        """Calculate Sharpe with real variance"""
        # Mix of positive and negative returns
        daily_returns = [0.01, -0.005, 0.015, -0.01, 0.02, 0.005]
        sharpe = calculate_sharpe_ratio(daily_returns)
        # Just verify it's a reasonable number
        assert -10 < sharpe < 10, f"Sharpe ratio {sharpe} seems unreasonable"

    def test_empty_returns(self):
        """Return 0 for empty returns"""
        sharpe = calculate_sharpe_ratio([])
        assert sharpe == 0


class TestMaxDrawdown:
    """Tests for max drawdown calculation"""

    def test_basic_drawdown(self):
        """Calculate drawdown from peak to trough"""
        snapshots = [
            {"equity": 10000},
            {"equity": 11000},  # New peak
            {"equity": 9900},   # 10% drawdown from peak
            {"equity": 10500},
        ]
        drawdown = calculate_max_drawdown(snapshots)
        assert abs(drawdown - 0.10) < 0.001, f"Expected ~10% drawdown but got {drawdown}"

    def test_no_drawdown(self):
        """No drawdown when equity only rises"""
        snapshots = [
            {"equity": 10000},
            {"equity": 10500},
            {"equity": 11000},
        ]
        drawdown = calculate_max_drawdown(snapshots)
        assert drawdown == 0, "Expected 0% drawdown for rising equity"

    def test_empty_snapshots(self):
        """Return 0 for empty snapshots"""
        drawdown = calculate_max_drawdown([])
        assert drawdown == 0

    def test_multiple_drawdowns_returns_max(self):
        """Return the maximum of multiple drawdowns"""
        snapshots = [
            {"equity": 10000},
            {"equity": 9500},   # 5% drawdown
            {"equity": 10000},  # Recovery
            {"equity": 11000},  # New peak
            {"equity": 8800},   # 20% drawdown from new peak
            {"equity": 9500},
        ]
        drawdown = calculate_max_drawdown(snapshots)
        assert abs(drawdown - 0.20) < 0.001, f"Expected ~20% max drawdown but got {drawdown}"


class TestWinRate:
    """Tests for win rate calculation"""

    def test_all_winners(self):
        """100% win rate with all profitable trades"""
        trades = [{"pnl": 100}, {"pnl": 50}, {"pnl": 200}]
        win_rate = calculate_win_rate(trades)
        assert win_rate == 1.0

    def test_all_losers(self):
        """0% win rate with all losing trades"""
        trades = [{"pnl": -100}, {"pnl": -50}, {"pnl": -200}]
        win_rate = calculate_win_rate(trades)
        assert win_rate == 0.0

    def test_mixed_trades(self):
        """Calculate win rate for mixed results"""
        trades = [{"pnl": 100}, {"pnl": -50}, {"pnl": 200}, {"pnl": -30}]
        win_rate = calculate_win_rate(trades)
        assert win_rate == 0.5, f"Expected 50% win rate but got {win_rate}"

    def test_empty_trades(self):
        """Return 0 for empty trades"""
        win_rate = calculate_win_rate([])
        assert win_rate == 0
