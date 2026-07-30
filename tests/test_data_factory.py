from datetime import datetime
import pytest
from services.data_factory.factory import DataSourceFactory
from services.data_factory.providers.base import MarketData
from services.data_factory.providers.binance import BinanceProvider
from services.data_factory.providers.yahoo import YahooProvider


class TestDataSourceFactory:
    def test_registry(self):
        assert "binance" in DataSourceFactory.list_providers()
        assert "yahoo" in DataSourceFactory.list_providers()

    def test_get_provider(self):
        assert isinstance(DataSourceFactory.get_provider("binance"), BinanceProvider)
        assert isinstance(DataSourceFactory.get_provider("yahoo"), YahooProvider)

    def test_invalid_provider(self):
        with pytest.raises(Exception):
            DataSourceFactory.get_provider("nonexistent")

    def test_market_data_dataclass(self):
        md = MarketData(symbol="BTCUSDT", provider="test", data_type="crypto", timestamp=datetime.now(), open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.5)
        assert md.symbol == "BTCUSDT"
        assert md.close == 50500.0
