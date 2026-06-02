from __future__ import annotations

from typing import Any
import requests

from app.kalshi_auth import KalshiAuth


class KalshiClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10, auth: KalshiAuth | None = None):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.auth = auth

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        auth_required: bool = False,
    ) -> Any:
        url = self._url(path)
        headers: dict[str, str] = {}
        if auth_required:
            if not self.auth:
                raise RuntimeError("Authenticated request attempted without credentials.")
            headers.update(self.auth.build_headers(method, url))
        if json is not None:
            headers["Content-Type"] = "application/json"
        response = requests.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def get_open_markets(self, limit: int = 25) -> list[dict[str, Any]]:
        data = self._request("GET", "/markets", params={"limit": limit, "status": "open"})
        return data.get("markets", [])

    def get_market_orderbook(self, ticker: str, depth: int = 5) -> dict[str, Any]:
        return self._request("GET", f"/markets/{ticker}/orderbook", params={"depth": depth})

    def get_balance(self) -> dict[str, Any]:
        return self._request("GET", "/portfolio/balance", auth_required=True)

    def get_positions(self) -> dict[str, Any]:
        return self._request("GET", "/portfolio/positions", auth_required=True)

    def get_orders(self, limit: int = 20) -> dict[str, Any]:
        return self._request("GET", "/portfolio/orders", params={"limit": limit}, auth_required=True)

    def place_limit_order(
        self,
        *,
        ticker: str,
        side: str,
        count: int,
        limit_price_cents: int,
        client_order_id: str,
    ) -> dict[str, Any]:
        payload = {
            "ticker": ticker,
            "action": "buy",
            "side": side,
            "count": count,
            "type": "limit",
            "client_order_id": client_order_id,
        }
        payload[f"{side}_price"] = limit_price_cents
        return self._request("POST", "/portfolio/orders", json=payload, auth_required=True)
