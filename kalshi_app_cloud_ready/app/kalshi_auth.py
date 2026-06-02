import base64
import time
from urllib.parse import urlparse

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class KalshiAuth:
    def __init__(self, api_key_id: str, private_key_path: str | None = None, private_key_pem: str | None = None):
        self.api_key_id = api_key_id
        self.private_key = self._load_private_key(private_key_path=private_key_path, private_key_pem=private_key_pem)

    @staticmethod
    def _load_private_key(private_key_path: str | None = None, private_key_pem: str | None = None):
        if private_key_pem:
            return serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"), password=None, backend=default_backend()
            )
        if private_key_path:
            with open(private_key_path, "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
        raise ValueError("A Kalshi private key must be provided via file path or KALSHI_PRIVATE_KEY environment variable.")

    def build_headers(self, method: str, full_url: str) -> dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        path = urlparse(full_url).path.split("?")[0]
        message = f"{timestamp}{method.upper()}{path}".encode("utf-8")
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        }
