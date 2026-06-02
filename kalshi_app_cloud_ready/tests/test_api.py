from pathlib import Path
import sys

from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.main as main
from app.kalshi_client import KalshiClient


client = TestClient(main.app)


class FakeClient:
    def get_balance(self):
        return {"balance": 1234}

    def get_positions(self):
        return {"market_positions": []}

    def get_orders(self, limit=20):
        return {"orders": [], "limit": limit}

    def get_open_markets(self, limit=25):
        return [
            {
                "ticker": "TEST-MARKET",
                "title": "Test market",
                "yes_bid_dollars": "0.42",
                "yes_ask_dollars": "0.47",
                "no_bid_dollars": "0.50",
                "no_ask_dollars": "0.55",
                "volume_24h_fp": "125.0",
                "open_interest_fp": "80.0",
                "liquidity_dollars": "900.0",
                "expiration_time": "2099-01-01T00:00:00Z",
            }
        ]

    def get_market_orderbook(self, ticker, depth=5):
        return {"orderbook_fp": {"yes_dollars": [["0.42", "15.0"]], "no_dollars": [["0.50", "12.0"]]}}

    def place_limit_order(self, **kwargs):
        return {"order": kwargs}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "kalshi_env" in body


def test_missing_credentials_returns_400_on_balance(monkeypatch):
    def fake_build_client(require_auth=False):
        raise HTTPException(status_code=400, detail="Missing Kalshi credentials in environment.")

    monkeypatch.setattr(main, "build_client", fake_build_client)
    response = client.get("/balance")
    assert response.status_code == 400


def test_missing_credentials_returns_400_on_order(monkeypatch):
    def fake_build_client(require_auth=False):
        raise HTTPException(status_code=400, detail="Missing Kalshi credentials in environment.")

    monkeypatch.setattr(main, "build_client", fake_build_client)
    response = client.post("/orders", json={"ticker": "TEST", "side": "yes", "count": 1, "limit_price_cents": 45})
    assert response.status_code == 400


def test_recommend_returns_schema(monkeypatch):
    monkeypatch.setattr(main, "build_client", lambda require_auth=False: FakeClient())
    response = client.post(
        "/recommend",
        json={
            "amount_dollars": 100,
            "market_limit": 10,
            "max_spread_cents": 10,
            "min_volume_24h": 0,
            "min_liquidity_dollars": 0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidate_count"] >= 1
    assert body["best_recommendation"]["ticker"] == "TEST-MARKET"
    assert "ranked_recommendations" in body


def test_signature_headers_present_for_auth_requests(monkeypatch):
    captured = {}

    class FakeAuth:
        def build_headers(self, method, full_url):
            return {
                "KALSHI-ACCESS-KEY": "key-id",
                "KALSHI-ACCESS-TIMESTAMP": "1234567890000",
                "KALSHI-ACCESS-SIGNATURE": "signed",
            }

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_request(method, url, params=None, json=None, headers=None, timeout=None):
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr("requests.request", fake_request)
    api = KalshiClient("https://external-api.demo.kalshi.co/trade-api/v2", auth=FakeAuth())
    result = api.get_balance()

    assert result == {"ok": True}
    assert captured["headers"]["KALSHI-ACCESS-KEY"] == "key-id"
    assert captured["headers"]["KALSHI-ACCESS-TIMESTAMP"] == "1234567890000"
    assert captured["headers"]["KALSHI-ACCESS-SIGNATURE"] == "signed"
