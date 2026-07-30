from __future__ import annotations
from typing import Dict, List
from shared.errors import NotFoundError
from .providers.base import BaseProvider, MarketData
from .providers.binance import BinanceProvider
from .providers.yahoo import YahooProvider


class DataSourceFactory:
    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        cls._registry[name] = provider_class

    @classmethod
    def get_provider(cls, name: str) -> BaseProvider:
        provider_class = cls._registry.get(name)
        if not provider_class:
            raise NotFoundError(f"Provider '{name}' not found. Available: {list(cls._registry.keys())}")
        return provider_class()

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    async def fetch_from_all(cls, symbol: str) -> Dict[str, MarketData]:
        results = {}
        for name in cls._registry:
            try:
                results[name] = await cls.get_provider(name).fetch_quote(symbol)
            except Exception:
                continue
        return results


DataSourceFactory.register("binance", BinanceProvider)
DataSourceFactory.register("yahoo", YahooProvider)
