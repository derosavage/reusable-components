from flask import Blueprint, jsonify, request
from .factory import DataSourceFactory

bp = Blueprint("data_factory", __name__)
factory = DataSourceFactory()

@bp.route("/quote", methods=["GET"])
async def get_quote():
    symbol = request.args.get("symbol", "").upper()
    provider_name = request.args.get("provider", "binance")
    if not symbol:
        return jsonify({"error": "symbol required"}), 400
    data = await factory.get_provider(provider_name).fetch_quote(symbol)
    return jsonify({"symbol": data.symbol, "provider": data.provider, "type": data.data_type, "timestamp": data.timestamp.isoformat(), "open": data.open, "high": data.high, "low": data.low, "close": data.close, "volume": data.volume, "extra": data.extra})

@bp.route("/historical", methods=["GET"])
async def get_historical():
    symbol = request.args.get("symbol", "").upper()
    provider_name = request.args.get("provider", "binance")
    interval = request.args.get("interval", "1h")
    limit = int(request.args.get("limit", 100))
    if not symbol:
        return jsonify({"error": "symbol required"}), 400
    data = await factory.get_provider(provider_name).fetch_historical(symbol, interval, limit)
    return jsonify([{"symbol": d.symbol, "provider": d.provider, "timestamp": d.timestamp.isoformat(), "open": d.open, "high": d.high, "low": d.low, "close": d.close, "volume": d.volume} for d in data])

@bp.route("/providers", methods=["GET"])
def list_providers():
    return jsonify({"providers": factory.list_providers()})

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "data-factory"})
