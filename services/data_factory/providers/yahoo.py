from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
import httpx
from .base import BaseProvider, MarketData

class YahooProvider(BaseProvider):
    BASE_URL = "https://query1.finance.yahoo.com"
    def __init__(self):
        super().__init__("yahoo")

    async def fetch_quote(self, symbol: str) -> MarketData:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/v8/finance/chart/{symbol.upper()}", params={"interval": "1d", "range": "1d"})
            resp.raise_for_status()
            data = resp.json()
        r = data["chart"]["result"][0]
        meta = r["meta"]
        q = r["indicators"]["quote"][0]
        ts = r["timestamp"][0]
        return MarketData(symbol=symbol.upper(), provider=self.name, data_type="stock", timestamp=datetime.fromtimestamp(ts), open=q.get("open", [0])[0] or 0, high=q.get("high", [0])[0] or 0, low=q.get("low", [0])[0] or 0, close=q.get("close", [0])[0] or meta.get("regularMarketPrice", 0), volume=q.get("volume", [0])[0] or 0, extra={"currency": meta.get("currency", "USD"), "exchange": meta.get("exchangeName", "")})

    async def fetch_historical(self, symbol: str, interval: str = "1d", limit: int = 100) -> List[MarketData]:
        ranges = {1: "1d", 5: "5d", 30: "1mo", 100: "3mo", 365: "1y"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/v8/finance/chart/{symbol.upper()}", params={"interval": interval, "range": ranges.get(limit, "1mo")})
            resp.raise_for_status()
            data = resp.json()
        r = data["chart"]["result"][0]
        timestamps = r["timestamp"]
        q = r["indicators"]["quote"][0]
        return [MarketData(symbol=symbol.upper(), provider=self.name, data_type="stock", timestamp=datetime.fromtimestamp(ts), open=q.get("open", [0])[i] or 0, high=q.get("high", [0])[i] or 0, low=q.get("low", [0])[i] or 0, close=q.get("close", [0])[i] or 0, volume=q.get("volume", [0])[i] or 0) for i, ts in enumerate(timestamps)]

    async def fetch_order_book(self, symbol: str) -> Dict[str, Any]:
        return {"provider": self.name, "detail": "Not available"}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                return (await client.get(f"{self.BASE_URL}/v8/finance/chart/AAPL?interval=1d&range=1d")).status_code == 200
        except Exception:
            return False
