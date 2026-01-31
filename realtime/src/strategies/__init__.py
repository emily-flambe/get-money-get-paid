from .base import Strategy, Signal
from .momentum import MomentumStrategy
from .mean_reversion import MeanReversionStrategy

STRATEGY_TYPES = {
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
}

def create_strategy(config: dict) -> Strategy:
    """Factory function to create strategy from config"""
    strategy_type = config["type"]
    if strategy_type not in STRATEGY_TYPES:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    return STRATEGY_TYPES[strategy_type](config)

__all__ = ["Strategy", "Signal", "create_strategy", "STRATEGY_TYPES"]
