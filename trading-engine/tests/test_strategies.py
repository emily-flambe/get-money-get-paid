"""
Tests for trading strategy logic in trading-engine.
"""
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trading_engine.strategies import (
    calculate_rsi,
    calculate_sma,
    calculate_momentum,
    should_buy_sma_crossover,
    should_sell_sma_crossover,
    should_buy_rsi,
    should_sell_rsi,
    should_buy_momentum,
    should_sell_momentum,
)


def create_bars(prices):
    """Create mock OHLCV bars from a list of closing prices"""
    return [{"o": p, "h": p, "l": p, "c": p, "v": 1000} for p in prices]


class TestCalculateRSI:
    """Tests for RSI calculation"""

    def test_rsi_overbought(self):
        """RSI should be high when prices consistently rise"""
        # Steadily rising prices
        bars = create_bars([100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                           120, 122, 124, 126, 128, 130])
        rsi = calculate_rsi(bars, 14)
        assert rsi > 70, f"RSI should be overbought (>70) but was {rsi}"

    def test_rsi_oversold(self):
        """RSI should be low when prices consistently fall"""
        # Steadily falling prices
        bars = create_bars([130, 128, 126, 124, 122, 120, 118, 116, 114, 112,
                           110, 108, 106, 104, 102, 100])
        rsi = calculate_rsi(bars, 14)
        assert rsi < 30, f"RSI should be oversold (<30) but was {rsi}"

    def test_rsi_no_losses_returns_100(self):
        """RSI should be 100 when there are only gains"""
        # Only gains, no losses
        bars = create_bars([100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
                           110, 111, 112, 113, 114, 115])
        rsi = calculate_rsi(bars, 14)
        assert rsi == 100, f"RSI should be 100 with only gains but was {rsi}"


class TestCalculateSMA:
    """Tests for SMA calculation"""

    def test_sma_basic(self):
        """Verify basic SMA calculation"""
        prices = [10, 20, 30, 40, 50]
        sma = calculate_sma(prices, 5)
        assert sma == 30.0, f"SMA should be 30.0 but was {sma}"

    def test_sma_last_n_prices(self):
        """SMA should only consider last N prices"""
        prices = [5, 10, 20, 30, 40, 50]
        sma = calculate_sma(prices, 3)
        assert sma == 40.0, f"SMA of last 3 prices should be 40.0 but was {sma}"

    def test_sma_insufficient_data(self):
        """SMA should return None with insufficient data"""
        prices = [10, 20]
        sma = calculate_sma(prices, 5)
        assert sma is None, "SMA should be None with insufficient data"


class TestSMACrossover:
    """Tests for SMA crossover strategy logic"""

    def test_buy_signal_when_short_above_long_no_position(self):
        """Should buy when short SMA > long SMA and no position"""
        assert should_buy_sma_crossover(40, 30, has_position=False) is True

    def test_no_buy_signal_when_already_has_position(self):
        """Should not buy when already has position"""
        assert should_buy_sma_crossover(40, 30, has_position=True) is False

    def test_no_buy_signal_when_short_below_long(self):
        """Should not buy when short SMA < long SMA"""
        assert should_buy_sma_crossover(25, 30, has_position=False) is False

    def test_sell_signal_when_short_below_long_has_position(self):
        """Should sell when short SMA < long SMA and has position"""
        assert should_sell_sma_crossover(25, 30, has_position=True) is True

    def test_no_sell_signal_when_no_position(self):
        """Should not sell when no position"""
        assert should_sell_sma_crossover(25, 30, has_position=False) is False


class TestMomentumStrategy:
    """Tests for momentum strategy logic"""

    def test_calculate_momentum_positive(self):
        """Calculate positive momentum correctly"""
        momentum = calculate_momentum(100, 110)
        assert momentum == 10.0

    def test_calculate_momentum_negative(self):
        """Calculate negative momentum correctly"""
        momentum = calculate_momentum(100, 90)
        assert momentum == -10.0

    def test_buy_signal_above_threshold(self):
        """Should buy when momentum > threshold and no position"""
        assert should_buy_momentum(10, 5, has_position=False) is True

    def test_no_buy_when_below_threshold(self):
        """Should not buy when momentum < threshold"""
        assert should_buy_momentum(3, 5, has_position=False) is False

    def test_sell_signal_below_negative_threshold(self):
        """Should sell when momentum < -threshold and has position"""
        assert should_sell_momentum(-10, 5, has_position=True) is True


class TestRSIStrategy:
    """Tests for RSI strategy logic"""

    def test_buy_signal_when_oversold(self):
        """Should buy when RSI < oversold threshold and no position"""
        assert should_buy_rsi(25, 30, has_position=False) is True

    def test_no_buy_when_not_oversold(self):
        """Should not buy when RSI > oversold threshold"""
        assert should_buy_rsi(50, 30, has_position=False) is False

    def test_sell_signal_when_overbought(self):
        """Should sell when RSI > overbought threshold and has position"""
        assert should_sell_rsi(75, 70, has_position=True) is True

    def test_no_sell_when_not_overbought(self):
        """Should not sell when RSI < overbought threshold"""
        assert should_sell_rsi(50, 70, has_position=True) is False
