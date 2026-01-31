import asyncio
import logging
import time
from typing import Optional
import httpx

from .strategies.base import Signal, SignalType

log = logging.getLogger(__name__)


class OrderManager:
    """
    Manages order execution with safety rails.

    Safety features:
    - Rate limiting (max orders per minute)
    - Per-symbol cooldown
    - Position size limits
    - Paper trading enforcement
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "https://paper-api.alpaca.markets",
        max_position_pct: float = 0.25,
        max_orders_per_minute: int = 10,
        cooldown_seconds: int = 5,
        paper_only: bool = True,
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.max_position_pct = max_position_pct
        self.max_orders_per_minute = max_orders_per_minute
        self.cooldown_seconds = cooldown_seconds
        self.paper_only = paper_only

        # Safety check - refuse to run against live API
        if paper_only and "paper" not in base_url:
            raise ValueError("Paper-only mode enabled but base_url doesn't contain 'paper'")

        # Rate limiting state
        self.orders_this_minute: list[float] = []
        self.last_order_time: dict[str, float] = {}

        # Account state (refreshed periodically)
        self.account_equity: float = 0
        self.positions: dict[str, dict] = {}

        # HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key,
            }
        )

    async def refresh_account(self):
        """Fetch current account and position data"""
        try:
            # Get account
            resp = await self.client.get(f"{self.base_url}/v2/account")
            resp.raise_for_status()
            account = resp.json()
            self.account_equity = float(account["equity"])

            # Get positions
            resp = await self.client.get(f"{self.base_url}/v2/positions")
            resp.raise_for_status()
            positions = resp.json()
            self.positions = {p["symbol"]: p for p in positions}

            log.debug(f"Account equity: ${self.account_equity:.2f}, positions: {list(self.positions.keys())}")

        except Exception as e:
            log.error(f"Failed to refresh account: {e}")

    async def submit(self, signal: Signal, dollar_amount: float) -> Optional[dict]:
        """
        Submit an order based on a signal.

        Returns order dict on success, None if blocked by safety checks.
        """
        # Clean up old rate limit entries
        now = time.time()
        self.orders_this_minute = [t for t in self.orders_this_minute if now - t < 60]

        # Safety check: rate limit
        if len(self.orders_this_minute) >= self.max_orders_per_minute:
            log.warning(f"Rate limit hit: {len(self.orders_this_minute)} orders in last minute")
            return None

        # Safety check: per-symbol cooldown
        last_order = self.last_order_time.get(signal.symbol, 0)
        if now - last_order < self.cooldown_seconds:
            log.debug(f"Cooldown active for {signal.symbol}")
            return None

        # Safety check: position size
        if signal.type == SignalType.BUY:
            current_position_value = 0
            if signal.symbol in self.positions:
                current_position_value = float(self.positions[signal.symbol]["market_value"])

            new_position_value = current_position_value + dollar_amount
            if self.account_equity > 0:
                position_pct = new_position_value / self.account_equity
                if position_pct > self.max_position_pct:
                    log.warning(
                        f"Position limit: {signal.symbol} would be {position_pct:.1%} of account "
                        f"(max {self.max_position_pct:.1%})"
                    )
                    return None

        # Build order
        order_data = {
            "symbol": signal.symbol,
            "side": signal.side,
            "type": "market",
            "time_in_force": "day",
        }

        if signal.type == SignalType.BUY:
            order_data["notional"] = str(round(dollar_amount, 2))
        else:
            # For sells, sell the entire position
            if signal.symbol in self.positions:
                order_data["qty"] = self.positions[signal.symbol]["qty"]
            else:
                log.warning(f"No position to sell for {signal.symbol}")
                return None

        # Submit order
        try:
            log.info(f"Submitting order: {order_data}")
            resp = await self.client.post(f"{self.base_url}/v2/orders", json=order_data)
            resp.raise_for_status()
            order = resp.json()

            # Update rate limiting state
            self.orders_this_minute.append(now)
            self.last_order_time[signal.symbol] = now

            log.info(f"Order submitted: {order['id']} - {order['side']} {order['symbol']}")
            return order

        except httpx.HTTPStatusError as e:
            log.error(f"Order failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            log.error(f"Order error: {e}")
            return None

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
