from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Signal:
    type: SignalType
    symbol: str
    strategy_name: str
    reason: str
    price: float
    timestamp: float

    @property
    def side(self) -> str:
        return self.type.value


class Strategy:
    """Base class for all trading strategies"""

    def __init__(self, config: dict):
        self.name = config["name"]
        self.symbols = config["symbols"]
        self.params = config.get("params", {})
        self.position_size_pct = config.get("position_size_pct", 0.1)
        self.cash_allocation = config.get("cash_allocation", 1000)
        self.enabled = config.get("enabled", True)

        # Track positions per symbol
        self.positions: dict[str, float] = {}  # symbol -> quantity

        # Cooldown tracking
        self.last_signal_time: dict[str, float] = {}
        self.cooldown_seconds = 5

    def has_position(self, symbol: str) -> bool:
        return self.positions.get(symbol, 0) > 0

    def get_position(self, symbol: str) -> float:
        return self.positions.get(symbol, 0)

    def update_position(self, symbol: str, quantity: float):
        self.positions[symbol] = quantity

    def in_cooldown(self, symbol: str) -> bool:
        last_time = self.last_signal_time.get(symbol, 0)
        return (time.time() - last_time) < self.cooldown_seconds

    def record_signal(self, symbol: str):
        self.last_signal_time[symbol] = time.time()

    def on_tick(self, symbol: str, price: float, indicators: dict) -> Optional[Signal]:
        """
        Called on every trade tick.

        Args:
            symbol: Stock symbol
            price: Current trade price
            indicators: Dict of computed indicators (momentum, vwap, etc.)

        Returns:
            Signal if action should be taken, None otherwise
        """
        raise NotImplementedError

    def on_bar(self, symbol: str, bar: dict, indicators: dict) -> Optional[Signal]:
        """
        Called on 1-minute bar close. Optional override.

        Args:
            symbol: Stock symbol
            bar: OHLCV bar data
            indicators: Dict of computed indicators

        Returns:
            Signal if action should be taken, None otherwise
        """
        return None

    def _make_signal(self, signal_type: SignalType, symbol: str, price: float, reason: str) -> Signal:
        """Helper to create a signal"""
        return Signal(
            type=signal_type,
            symbol=symbol,
            strategy_name=self.name,
            reason=reason,
            price=price,
            timestamp=time.time(),
        )
