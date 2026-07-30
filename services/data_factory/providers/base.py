from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

@dataclass
class MarketData:
    symbol: str
    provider: str
    data_type: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def fetch_quote(self, symbol: str) -> MarketData:
        ...

    @abstractmethod
    async def fetch_historical(self, symbol: str, interval: str, limit: int = 100) -> List[MarketData]:
        ...

    @abstractmethod
    async def fetch_order_book(self, symbol: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
