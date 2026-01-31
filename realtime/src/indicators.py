import time
from collections import deque
from dataclasses import dataclass
from typing import Optional
import statistics


@dataclass
class Tick:
    price: float
    size: int
    timestamp: float


class TickBuffer:
    """
    Rolling buffer of ticks per symbol with computed indicators.

    Maintains a time-based window (not count-based) for accurate
    time-series indicators.
    """

    def __init__(self, max_age_seconds: int = 120):
        self.max_age_seconds = max_age_seconds
        self.buffers: dict[str, deque[Tick]] = {}

    def add(self, symbol: str, price: float, size: int, timestamp: float = None):
        """Add a tick to the buffer"""
        if symbol not in self.buffers:
            self.buffers[symbol] = deque()

        tick = Tick(
            price=price,
            size=size,
            timestamp=timestamp or time.time(),
        )
        self.buffers[symbol].append(tick)

        # Prune old ticks
        self._prune(symbol)

    def _prune(self, symbol: str):
        """Remove ticks older than max_age_seconds"""
        cutoff = time.time() - self.max_age_seconds
        buffer = self.buffers[symbol]
        while buffer and buffer[0].timestamp < cutoff:
            buffer.popleft()

    def get_indicators(self, symbol: str) -> dict:
        """
        Compute indicators for a symbol.

        Returns dict with keys like:
            - momentum_5s: % price change over last 5 seconds
            - momentum_10s: % price change over last 10 seconds
            - mean_60s: Mean price over last 60 seconds
            - std_60s: Std dev of price over last 60 seconds
            - vwap: Volume-weighted average price
            - tick_count: Number of ticks in buffer
        """
        if symbol not in self.buffers or len(self.buffers[symbol]) < 2:
            return {}

        buffer = self.buffers[symbol]
        now = time.time()

        indicators = {
            "tick_count": len(buffer),
            "last_price": buffer[-1].price,
        }

        # Momentum at various intervals
        for seconds in [5, 10, 15, 30, 60]:
            momentum = self._calc_momentum(buffer, now, seconds)
            if momentum is not None:
                indicators[f"momentum_{seconds}s"] = momentum

        # Mean and std at various intervals
        for seconds in [30, 60, 120]:
            prices = self._get_prices_in_window(buffer, now, seconds)
            if len(prices) >= 5:
                indicators[f"mean_{seconds}s"] = statistics.mean(prices)
                indicators[f"std_{seconds}s"] = statistics.stdev(prices) if len(prices) > 1 else 0

        # VWAP
        vwap = self._calc_vwap(buffer)
        if vwap:
            indicators["vwap"] = vwap

        return indicators

    def _calc_momentum(self, buffer: deque[Tick], now: float, seconds: int) -> Optional[float]:
        """Calculate % price change over last N seconds"""
        cutoff = now - seconds

        # Find first tick within window
        old_price = None
        for tick in buffer:
            if tick.timestamp >= cutoff:
                old_price = tick.price
                break

        if old_price is None or old_price == 0:
            return None

        current_price = buffer[-1].price
        return ((current_price - old_price) / old_price) * 100

    def _get_prices_in_window(self, buffer: deque[Tick], now: float, seconds: int) -> list[float]:
        """Get all prices within time window"""
        cutoff = now - seconds
        return [t.price for t in buffer if t.timestamp >= cutoff]

    def _calc_vwap(self, buffer: deque[Tick]) -> Optional[float]:
        """Calculate volume-weighted average price"""
        total_value = 0
        total_volume = 0

        for tick in buffer:
            total_value += tick.price * tick.size
            total_volume += tick.size

        if total_volume == 0:
            return None

        return total_value / total_volume
