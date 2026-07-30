from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
import httpx
from .base import BaseProvider, MarketData

class BinanceProvider(BaseProvider):
    BASE_URL = "https://api.binance.com"
    def __init__(self):
        super().__init__("binance")

    async def fetch_quote(self, symbol: str) -> MarketData:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/api/v3/ticker/24hr", params={"symbol": symbol.upper()})
            resp.raise_for_status()
            d = resp.json()
        return MarketData(symbol=symbol.upper(), provider=self.name, data_type="crypto", timestamp=datetime.fromtimestamp(d["closeTime"] / 1000), open=float(d["openPrice"]), high=float(d["highPrice"]), low=float(d["lowPrice"]), close=float(d["lastPrice"]), volume=float(d["volume"]), extra={"price_change": float(d["priceChange"]), "price_change_percent": float(d["priceChangePercent"])})

    async def fetch_historical(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[MarketData]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/api/v3/klines", params={"symbol": symbol.upper(), "interval": interval, "limit": limit})
            resp.raise_for_status()
            candles = resp.json()
        return [MarketData(symbol=symbol.upper(), provider=self.name, data_type="crypto", timestamp=datetime.fromtimestamp(c[0] / 1000), open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]), volume=float(c[5])) for c in candles]

    async def fetch_order_book(self, symbol: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/api/v3/depth", params={"symbol": symbol.upper(), "limit": 10})
            resp.raise_for_status()
            return resp.json()

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                return (await client.get(f"{self.BASE_URL}/api/v3/ping")).status_code == 200
        except Exception:
            return False
