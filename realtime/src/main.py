#!/usr/bin/env python3
"""
Real-time trading engine entry point.

Usage:
    python -m src.main
    python -m src.main --config /path/to/config
"""
import argparse
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import yaml

from .websocket import AlpacaWebSocket
from .indicators import TickBuffer
from .orders import OrderManager
from .engine import TradingEngine
from .strategies import create_strategy

log = logging.getLogger(__name__)


def load_config(config_dir: Path) -> tuple[dict, list[dict]]:
    """Load settings and strategies from config files"""
    settings_path = config_dir / "settings.yaml"
    strategies_path = config_dir / "strategies.yaml"

    with open(settings_path) as f:
        settings = yaml.safe_load(f)

    with open(strategies_path) as f:
        strategies_config = yaml.safe_load(f)

    # Expand environment variables in settings
    settings = expand_env_vars(settings)

    return settings, strategies_config.get("strategies", [])


def expand_env_vars(obj):
    """Recursively expand ${VAR} in config values"""
    if isinstance(obj, dict):
        return {k: expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_env_vars(v) for v in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        return os.environ.get(var_name, obj)
    return obj


def setup_logging(level: str = "INFO"):
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def run_engine(settings: dict, strategy_configs: list[dict]):
    """Initialize and run the trading engine"""

    # Create strategies
    strategies = []
    for config in strategy_configs:
        if config.get("enabled", True):
            try:
                strategy = create_strategy(config)
                strategies.append(strategy)
                log.info(f"Loaded strategy: {strategy.name} ({config['type']})")
            except Exception as e:
                log.error(f"Failed to load strategy {config.get('name', 'unknown')}: {e}")

    if not strategies:
        log.error("No strategies loaded!")
        return

    # Create WebSocket client
    ws = AlpacaWebSocket(
        api_key=settings["alpaca"]["api_key"],
        secret_key=settings["alpaca"]["secret_key"],
        data_url=settings["alpaca"]["data_url"],
    )

    # Create order manager
    safety = settings.get("safety", {})
    orders = OrderManager(
        api_key=settings["alpaca"]["api_key"],
        secret_key=settings["alpaca"]["secret_key"],
        base_url=settings["alpaca"]["base_url"],
        max_position_pct=safety.get("max_position_pct", 0.25),
        max_orders_per_minute=safety.get("max_orders_per_minute", 10),
        cooldown_seconds=safety.get("cooldown_seconds", 5),
        paper_only=safety.get("paper_only", True),
    )

    # Create tick buffer
    tick_buffer = TickBuffer(max_age_seconds=120)

    # Create engine
    engine = TradingEngine(
        websocket=ws,
        order_manager=orders,
        strategies=strategies,
        tick_buffer=tick_buffer,
    )

    # Handle shutdown gracefully
    loop = asyncio.get_event_loop()

    def shutdown_handler():
        log.info("Shutdown signal received")
        asyncio.create_task(engine.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_handler)

    # Run
    try:
        await engine.run()
    except KeyboardInterrupt:
        log.info("Interrupted")
    finally:
        await engine.stop()


def main():
    parser = argparse.ArgumentParser(description="Real-time trading engine")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent.parent / "config",
        help="Config directory path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)
    log.info(f"Loading config from {args.config}")

    settings, strategy_configs = load_config(args.config)
    log.info(f"Loaded {len(strategy_configs)} strategy configs")

    asyncio.run(run_engine(settings, strategy_configs))


if __name__ == "__main__":
    main()
