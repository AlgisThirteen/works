from pydantic import BaseModel, Field
from typing import Literal


class RecommendRequest(BaseModel):
    amount_dollars: float = Field(gt=0)
    market_limit: int = Field(default=25, ge=1, le=100)
    max_spread_cents: int = Field(default=20, ge=1, le=99)
    min_depth_contracts: float = Field(default=0, ge=0)
    orderbook_depth_cents: int = Field(default=5, ge=1, le=25)
    min_volume_24h: float = Field(default=0, ge=0)
    min_liquidity_dollars: float = Field(default=0, ge=0)
    max_hours_to_expiry: float | None = Field(default=None, gt=0)
    market_query: str | None = Field(default=None, max_length=120)
    use_orderbook_refinement: bool = False


class PlaceOrderRequest(BaseModel):
    ticker: str
    side: Literal["yes", "no"]
    count: int = Field(gt=0)
    limit_price_cents: int = Field(ge=1, le=99)
    action: Literal["buy"] = "buy"
    client_order_id: str | None = None
