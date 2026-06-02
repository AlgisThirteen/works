from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.kalshi_auth import KalshiAuth
from app.kalshi_client import KalshiClient
from app.models import PlaceOrderRequest, RecommendRequest
from app.strategy import market_matches_query, score_market, serialize_recommendation

app = FastAPI(title="Kalshi Recommendation Starter")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def build_client(require_auth: bool = False) -> KalshiClient:
    settings = get_settings()
    auth = None
    if require_auth:
        if not settings.api_key_id or not (settings.private_key_pem or settings.private_key_path):
            raise HTTPException(status_code=400, detail="Missing Kalshi credentials in environment.")
        if settings.private_key_pem:
            auth = KalshiAuth(settings.api_key_id, private_key_pem=settings.private_key_pem)
        else:
            key_path = Path(settings.private_key_path).expanduser()
            if not key_path.exists():
                raise HTTPException(status_code=400, detail=f"Kalshi private key file not found: {key_path}")
            auth = KalshiAuth(settings.api_key_id, private_key_path=str(key_path))
    return KalshiClient(settings.base_url, timeout_seconds=settings.request_timeout_seconds, auth=auth)


@app.get("/")
def index():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "kalshi_env": settings.kalshi_env,
        "base_url": settings.base_url,
        "auth_configured": settings.auth_configured,
        "private_key_exists": settings.private_key_exists,
        "private_key_source": settings.private_key_source,
    }


@app.get("/balance")
def balance():
    try:
        client = build_client(require_auth=True)
        return client.get_balance()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/positions")
def positions():
    try:
        client = build_client(require_auth=True)
        return client.get_positions()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/orders")
def list_orders(limit: int = Query(default=20, ge=1, le=100)):
    try:
        client = build_client(require_auth=True)
        return client.get_orders(limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/recommend")
def recommend(request: RecommendRequest):
    try:
        client = build_client(require_auth=False)
        fetch_limit = 100
        markets = client.get_open_markets(limit=fetch_limit)
        filtered_markets = [m for m in markets if market_matches_query(m, request.market_query)]
        ranked: list[dict] = []
        note = "This starter now ranks markets from public quote snapshots using spread, liquidity, 24h volume, affordability, and optional orderbook refinement. Replace it with your own probability model before live trading."

        for market in filtered_markets:
            recommendation = score_market(
                market=market,
                amount_dollars=request.amount_dollars,
                max_spread_cents=request.max_spread_cents,
                min_volume_24h=request.min_volume_24h,
                min_liquidity_dollars=request.min_liquidity_dollars,
                max_hours_to_expiry=request.max_hours_to_expiry,
            )
            if recommendation:
                ranked.append(serialize_recommendation(recommendation))

        ranked.sort(key=lambda x: x["heuristic_score"], reverse=True)

        if not ranked:
            fallback_ranked: list[dict] = []
            for market in filtered_markets:
                recommendation = score_market(
                    market=market,
                    amount_dollars=request.amount_dollars,
                    max_spread_cents=99,
                    min_volume_24h=0,
                    min_liquidity_dollars=0,
                    max_hours_to_expiry=request.max_hours_to_expiry,
                )
                if recommendation:
                    fallback_ranked.append(serialize_recommendation(recommendation))
            fallback_ranked.sort(key=lambda x: x["heuristic_score"], reverse=True)
            if fallback_ranked:
                ranked = fallback_ranked
                note = "No markets passed your requested spread and liquidity filters, so the API returned the best available fallback candidates from current quote snapshots. These are demonstration candidates only and may still be too wide to trade."

        if request.use_orderbook_refinement and ranked:
            refined: list[dict] = []
            market_lookup = {market.get("ticker"): market for market in filtered_markets}
            for row in ranked[:10]:
                market = market_lookup.get(row["ticker"])
                if not market:
                    refined.append(row)
                    continue
                try:
                    orderbook = client.get_market_orderbook(row["ticker"], depth=request.orderbook_depth_cents)
                    rescored = score_market(
                        market=market,
                        amount_dollars=request.amount_dollars,
                        max_spread_cents=request.max_spread_cents,
                        min_volume_24h=request.min_volume_24h,
                        min_liquidity_dollars=request.min_liquidity_dollars,
                        max_hours_to_expiry=request.max_hours_to_expiry,
                        orderbook=orderbook,
                        min_depth_contracts=request.min_depth_contracts,
                        depth_cents=request.orderbook_depth_cents,
                    )
                    if rescored:
                        refined.append(serialize_recommendation(rescored))
                except Exception:
                    refined.append(row)
            tickers = {row["ticker"] for row in refined}
            ranked = refined + [row for row in ranked if row["ticker"] not in tickers]
            ranked.sort(key=lambda x: x["heuristic_score"], reverse=True)

        ranked = ranked[: request.market_limit]
        return {
            "amount_dollars": request.amount_dollars,
            "scanned_market_count": len(filtered_markets),
            "candidate_count": len(ranked),
            "best_recommendation": ranked[0] if ranked else None,
            "ranked_recommendations": ranked,
            "note": note,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/orders")
def place_order(request: PlaceOrderRequest):
    try:
        client = build_client(require_auth=True)
        result = client.place_limit_order(
            ticker=request.ticker,
            side=request.side,
            count=request.count,
            limit_price_cents=request.limit_price_cents,
            client_order_id=request.client_order_id or str(uuid.uuid4()),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
