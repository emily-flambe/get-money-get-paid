"""
D1 Sync - Sync trades to the Cloudflare dashboard API
"""
import logging
import aiohttp
from typing import Optional

log = logging.getLogger(__name__)

DASHBOARD_API_URL = "https://stonks.emilycogsdill.com"


class D1Sync:
    """Syncs trades to the dashboard D1 database via API"""

    def __init__(self, api_url: str = DASHBOARD_API_URL):
        self.api_url = api_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def record_trade(
        self,
        algorithm_id: str,
        symbol: str,
        side: str,
        quantity: float,
        alpaca_order_id: str,
        status: str,
        filled_price: float,
        filled_qty: float,
        notes: str = "",
    ) -> bool:
        """Record a trade to the dashboard API"""
        try:
            session = await self._get_session()
            payload = {
                "algorithm_id": algorithm_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": "market",
                "status": status,
                "alpaca_order_id": alpaca_order_id,
                "notes": notes,
                "filled_price": filled_price,
                "filled_qty": filled_qty,
            }

            async with session.post(
                f"{self.api_url}/api/trades",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    log.info(f"Trade synced to D1: {result.get('id')}")
                    return True
                else:
                    text = await response.text()
                    log.error(f"Failed to sync trade: {response.status} - {text}")
                    return False

        except Exception as e:
            log.error(f"D1 sync error: {e}")
            return False

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
