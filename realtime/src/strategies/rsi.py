from typing import Optional
from collections import deque
from .base import Strategy, Signal, SignalType


class RSIStrategy(Strategy):
    """
    RSI Mean Reversion strategy - buy oversold, sell overbought.

    RSI measures the speed and magnitude of price changes.
    - RSI < 30: Oversold (potential buy)
    - RSI > 70: Overbought (potential sell)

    For real-time, we calculate RSI from recent ticks.

    Params:
        period: Number of price changes for RSI calculation (default 14)
        oversold: RSI threshold for buy signal (default 30)
        overbought: RSI threshold for sell signal (default 70)
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.period = self.params.get("period", 14)
        self.oversold = self.params.get("oversold", 30)
        self.overbought = self.params.get("overbought", 70)

        # Track recent prices for RSI calculation
        self.prices: dict[str, deque] = {}

    def _calc_rsi(self, symbol: str, price: float) -> Optional[float]:
        """Calculate RSI from recent price changes"""
        if symbol not in self.prices:
            self.prices[symbol] = deque(maxlen=self.period + 1)

        self.prices[symbol].append(price)

        if len(self.prices[symbol]) < self.period + 1:
            return None

        # Calculate gains and losses
        gains = []
        losses = []
        prices = list(self.prices[symbol])

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-self.period:]) / self.period
        avg_loss = sum(losses[-self.period:]) / self.period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def on_tick(self, symbol: str, price: float, indicators: dict) -> Optional[Signal]:
        rsi = self._calc_rsi(symbol, price)

        if rsi is None:
            return None

        if self.in_cooldown(symbol):
            return None

        # Oversold - buy signal
        if rsi < self.oversold and not self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.BUY,
                symbol,
                price,
                f"RSI oversold: {rsi:.1f} < {self.oversold}"
            )

        # Overbought - sell signal
        if rsi > self.overbought and self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.SELL,
                symbol,
                price,
                f"RSI overbought: {rsi:.1f} > {self.overbought}"
            )

        return None
