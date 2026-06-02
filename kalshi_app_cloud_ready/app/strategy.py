from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import floor
from typing import Any


@dataclass
class Recommendation:
    ticker: str
    title: str
    side: str
    best_bid_cents: int
    best_ask_cents: int
    spread_cents: int
    top_depth_contracts: float | None
    affordable_contracts: int
    estimated_cost_dollars: float
    heuristic_score: float
    liquidity_dollars: float
    volume_24h_contracts: float
    open_interest_contracts: float
    hours_to_expiry: float | None
    rationale: str


def _to_cents(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(round(float(value) * 100))


def _to_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    normalized = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def hours_to_expiry(market: dict[str, Any]) -> float | None:
    expiry = _parse_iso(market.get("expiration_time") or market.get("close_time"))
    if not expiry:
        return None
    delta = expiry - datetime.now(timezone.utc)
    return round(delta.total_seconds() / 3600, 2)


def _parse_levels(levels: list[list[str]]) -> list[tuple[int, float]]:
    parsed: list[tuple[int, float]] = []
    for price_str, count_str in levels:
        parsed.append((_to_cents(price_str) or 0, float(count_str)))
    return parsed


def _best_bid(levels: list[tuple[int, float]]) -> tuple[int, float] | None:
    if not levels:
        return None
    return levels[-1]


def _depth_within(levels: list[tuple[int, float]], best_price: int, depth_cents: int) -> float:
    total = 0.0
    for price, count in reversed(levels):
        if best_price - price <= depth_cents:
            total += count
        else:
            break
    return round(total, 2)


def _orderbook_depth_for_side(orderbook: dict[str, Any] | None, side: str, depth_cents: int) -> float | None:
    if not orderbook:
        return None
    book = orderbook.get("orderbook_fp", {})
    levels = _parse_levels(book.get(f"{side}_dollars", []))
    best = _best_bid(levels)
    if not best:
        return None
    best_bid, _ = best
    return _depth_within(levels, best_bid, depth_cents)


def market_matches_query(market: dict[str, Any], market_query: str | None) -> bool:
    if not market_query:
        return True
    query = market_query.lower().strip()
    haystack = " ".join(
        [
            str(market.get("ticker", "")),
            str(market.get("title", "")),
            str(market.get("subtitle", "")),
            str(market.get("event_ticker", "")),
        ]
    ).lower()
    return query in haystack


def score_market(
    market: dict[str, Any],
    *,
    amount_dollars: float,
    max_spread_cents: int,
    min_volume_24h: float = 0.0,
    min_liquidity_dollars: float = 0.0,
    max_hours_to_expiry: float | None = None,
    orderbook: dict[str, Any] | None = None,
    min_depth_contracts: float = 0.0,
    depth_cents: int = 5,
) -> Recommendation | None:
    liquidity_dollars = _to_float(market.get("liquidity_dollars"))
    volume_24h_contracts = _to_float(market.get("volume_24h_fp"))
    open_interest_contracts = _to_float(market.get("open_interest_fp"))
    expiry_hours = hours_to_expiry(market)

    if liquidity_dollars < min_liquidity_dollars or volume_24h_contracts < min_volume_24h:
        return None
    if max_hours_to_expiry is not None and expiry_hours is not None and expiry_hours > max_hours_to_expiry:
        return None

    yes_bid = _to_cents(market.get("yes_bid_dollars"))
    yes_ask = _to_cents(market.get("yes_ask_dollars"))
    no_bid = _to_cents(market.get("no_bid_dollars"))
    no_ask = _to_cents(market.get("no_ask_dollars"))

    candidates: list[dict[str, Any]] = []
    for side, bid, ask in (("yes", yes_bid, yes_ask), ("no", no_bid, no_ask)):
        if bid is None or ask is None:
            continue
        if ask < 1 or ask > 99:
            continue
        if bid < 0 or bid >= ask:
            continue
        spread = ask - bid
        if spread > max_spread_cents:
            continue

        price_dollars = ask / 100
        affordable_contracts = floor(amount_dollars / price_dollars) if price_dollars > 0 else 0
        if affordable_contracts <= 0:
            continue

        top_depth_contracts = _orderbook_depth_for_side(orderbook, side, depth_cents)
        if min_depth_contracts > 0 and top_depth_contracts is not None and top_depth_contracts < min_depth_contracts:
            continue

        tightness_score = max(0.0, 1 - (spread / max(max_spread_cents, 1)))
        liquidity_score = min(liquidity_dollars / 2500.0, 1.0)
        volume_score = min(volume_24h_contracts / 1000.0, 1.0)
        interest_score = min(open_interest_contracts / 1000.0, 1.0)
        affordability_score = min(affordable_contracts / 50.0, 1.0)
        depth_score = 0.5 if top_depth_contracts is None else min(top_depth_contracts / max(min_depth_contracts, 10.0), 1.0)

        heuristic_score = round(
            (0.38 * tightness_score)
            + (0.18 * liquidity_score)
            + (0.16 * volume_score)
            + (0.10 * interest_score)
            + (0.10 * affordability_score)
            + (0.08 * depth_score),
            4,
        )

        rationale_parts = [
            f"{side.upper()} spread={spread}c",
            f"liquidity=${liquidity_dollars:.2f}",
            f"24h volume≈{volume_24h_contracts:.2f}",
            f"affordable contracts={affordable_contracts}",
        ]
        if expiry_hours is not None:
            rationale_parts.append(f"hours to expiry≈{expiry_hours:.2f}")
        if top_depth_contracts is not None:
            rationale_parts.append(f"orderbook depth≈{top_depth_contracts:.2f} within {depth_cents}c")

        candidates.append(
            {
                "side": side,
                "best_bid": bid,
                "best_ask": ask,
                "spread": spread,
                "top_depth": top_depth_contracts,
                "affordable_contracts": affordable_contracts,
                "estimated_cost": round(affordable_contracts * price_dollars, 2),
                "score": heuristic_score,
                "rationale": "; ".join(rationale_parts),
            }
        )

    if not candidates:
        return None

    chosen = max(candidates, key=lambda x: x["score"])
    return Recommendation(
        ticker=market.get("ticker", ""),
        title=market.get("title", market.get("subtitle", "Untitled market")),
        side=chosen["side"],
        best_bid_cents=chosen["best_bid"],
        best_ask_cents=chosen["best_ask"],
        spread_cents=chosen["spread"],
        top_depth_contracts=chosen["top_depth"],
        affordable_contracts=chosen["affordable_contracts"],
        estimated_cost_dollars=chosen["estimated_cost"],
        heuristic_score=chosen["score"],
        liquidity_dollars=round(liquidity_dollars, 2),
        volume_24h_contracts=round(volume_24h_contracts, 2),
        open_interest_contracts=round(open_interest_contracts, 2),
        hours_to_expiry=expiry_hours,
        rationale=chosen["rationale"],
    )


def serialize_recommendation(rec: Recommendation) -> dict[str, Any]:
    return asdict(rec)
