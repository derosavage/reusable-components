from flask import Blueprint, jsonify, request
from .daraja import DarajaClient

bp = Blueprint("daraja", __name__)
client = DarajaClient()


@bp.route("/stk-push", methods=["POST"])
async def stk_push():
    data = request.get_json()
    phone, amount = data.get("phone_number", ""), data.get("amount", 0)
    if not phone or amount <= 0:
        return jsonify({"error": "phone_number and amount required"}), 400
    result = await client.stk_push(phone, amount, data.get("account_reference", "ref"))
    return jsonify(result)


@bp.route("/query", methods=["POST"])
async def query():
    checkout_id = request.get_json().get("checkout_request_id", "")
    if not checkout_id:
        return jsonify({"error": "checkout_request_id required"}), 400
    result = await client.query_status(checkout_id)
    return jsonify(result)


@bp.route("/b2c", methods=["POST"])
async def b2c():
    data = request.get_json()
    phone, amount = data.get("phone_number", ""), data.get("amount", 0)
    if not phone or amount <= 0:
        return jsonify({"error": "phone_number and amount required"}), 400
    result = await client.b2c_payment(phone, amount)
    return jsonify(result)


@bp.route("/callback", methods=["POST"])
def callback():
    body = request.get_json().get("Body", {}).get("stkCallback", {})
    return jsonify({
        "ResultCode": 0,
        "ResultDesc": "Success",
        "checkout_request_id": body.get("CheckoutRequestID"),
        "result_code": body.get("ResultCode"),
    })


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "daraja"})