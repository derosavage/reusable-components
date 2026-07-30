from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from shared.config import settings


class DarajaClient:
    """Safaricom Daraja (M-Pesa) API client.

    Architecture:
      Client -> Queue -> Worker -> Daraja -> Callback -> Webhook -> Database

    Never call this directly in the request/response cycle.
    Use background workers via Celery.
    """

    BASE_URLS = {
        "sandbox": "https://sandbox.safaricom.co.ke",
        "production": "https://api.safaricom.co.ke",
    }

    def __init__(self):
        self.base_url = self.BASE_URLS.get(settings.DARAJA_ENV, self.BASE_URLS["sandbox"])
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _generate_password(self, timestamp: str) -> str:
        raw = f"{settings.DARAJA_SHORTCODE}{settings.DARAJA_PASSKEY}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def _generate_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S")

    async def _get_access_token(self) -> str:
        if self._access_token and self._token_expiry and datetime.now(timezone.utc) < self._token_expiry:
            return self._access_token

        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=(settings.DARAJA_CONSUMER_KEY, settings.DARAJA_CONSUMER_SECRET))
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 3599)
            from datetime import timedelta
            self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
            return self._access_token

    async def stk_push(self, phone_number: str, amount: float, account_reference: str, transaction_desc: str = "Payment") -> Dict[str, Any]:
        token = await self._get_access_token()
        timestamp = self._generate_timestamp()
        password = self._generate_password(timestamp)

        payload = {
            "BusinessShortCode": settings.DARAJA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": round(amount),
            "PartyA": phone_number,
            "PartyB": settings.DARAJA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.DARAJA_CALLBACK_URL,
            "AccountReference": account_reference[:12],
            "TransactionDesc": transaction_desc[:13],
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def query_status(self, checkout_request_id: str) -> Dict[str, Any]:
        token = await self._get_access_token()
        timestamp = self._generate_timestamp()
        payload = {
            "BusinessShortCode": settings.DARAJA_SHORTCODE,
            "Password": self._generate_password(timestamp),
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def b2c_payment(self, phone_number: str, amount: float, occasion: str = "Payment", remarks: str = "Business Payment") -> Dict[str, Any]:
        token = await self._get_access_token()
        payload = {
            "InitiatorName": settings.DARAJA_CONSUMER_KEY,
            "SecurityCredential": settings.DARAJA_CONSUMER_SECRET,
            "CommandID": "BusinessPayment",
            "Amount": round(amount),
            "PartyA": settings.DARAJA_SHORTCODE,
            "PartyB": phone_number,
            "Remarks": remarks[:100],
            "QueueTimeOutURL": settings.DARAJA_CALLBACK_URL.replace("callback", "timeout"),
            "ResultURL": settings.DARAJA_CALLBACK_URL.replace("callback", "result"),
            "Occasion": occasion[:100],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/mpesa/b2c/v1/paymentrequest",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()