from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    kalshi_env: str = os.getenv("KALSHI_ENV", "demo").lower()
    api_key_id: str | None = os.getenv("KALSHI_API_KEY_ID")
    private_key_path: str | None = os.getenv("KALSHI_PRIVATE_KEY_PATH")
    private_key_pem: str | None = os.getenv("KALSHI_PRIVATE_KEY")
    request_timeout_seconds: int = int(os.getenv("KALSHI_REQUEST_TIMEOUT_SECONDS", "10"))
    default_market_limit: int = int(os.getenv("DEFAULT_MARKET_LIMIT", "25"))
    default_max_spread_cents: int = int(os.getenv("DEFAULT_MAX_SPREAD_CENTS", "20"))
    default_min_depth_contracts: float = float(os.getenv("DEFAULT_MIN_DEPTH_CONTRACTS", "0"))
    default_orderbook_depth_cents: int = int(os.getenv("DEFAULT_ORDERBOOK_DEPTH_CENTS", "5"))
    default_min_volume_24h: float = float(os.getenv("DEFAULT_MIN_VOLUME_24H", "0"))
    default_min_liquidity_dollars: float = float(os.getenv("DEFAULT_MIN_LIQUIDITY_DOLLARS", "0"))

    @property
    def base_url(self) -> str:
        if self.kalshi_env == "production":
            return "https://external-api.kalshi.com/trade-api/v2"
        return "https://external-api.demo.kalshi.co/trade-api/v2"

    @property
    def auth_configured(self) -> bool:
        return bool(self.api_key_id and (self.private_key_pem or self.private_key_path))

    @property
    def private_key_source(self) -> str:
        if self.private_key_pem:
            return "env"
        if self.private_key_path:
            return "path"
        return "missing"

    @property
    def private_key_exists(self) -> bool:
        if self.private_key_pem:
            return True
        if not self.private_key_path:
            return False
        return Path(self.private_key_path).expanduser().exists()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
