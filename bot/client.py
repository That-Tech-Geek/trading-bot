import hashlib
import hmac
import time
import logging

import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """Thin wrapper around the Binance Futures Testnet REST API."""

    BASE_URL = "https://testnet.binancefuture.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
        })

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _generate_signature(self, params: dict) -> str:
        """HMAC-SHA256 signature required by signed endpoints."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        params: dict | None = None,
    ):
        """Send a request to the Binance Futures API.

        For signed requests the timestamp, recvWindow, and signature are
        appended automatically.  All parameters are sent as a query-string
        (even for POST) which is the format Binance expects.
        """
        url = f"{self.BASE_URL}{endpoint}"
        if params is None:
            params = {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params["signature"] = self._generate_signature(params)

        # Binance REST API expects parameters in the query-string for all
        # methods, including POST.
        full_url = f"{url}?{urlencode(params)}" if params else url
        response = self.session.request(method, full_url)

        logger.debug(
            "Request: %s %s | Params: %s | Status: %s",
            method, url, params, response.status_code,
        )

        if response.status_code != 200:
            logger.error("API error: %s", response.text)
            response.raise_for_status()

        return response.json()

    # ------------------------------------------------------------------ #
    # Public methods
    # ------------------------------------------------------------------ #

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
    ) -> dict:
        """Place an order on Binance Futures Testnet.

        Parameters
        ----------
        symbol : str
            Trading pair, e.g. ``BTCUSDT``.
        side : str
            ``BUY`` or ``SELL``.
        order_type : str
            ``MARKET`` or ``LIMIT``.
        quantity : float
            Order quantity in the base asset.
        price : float, optional
            Required for ``LIMIT`` orders.

        Returns
        -------
        dict
            Parsed JSON response from the API (``RESULT`` response type).
        """
        endpoint = "/fapi/v1/order"
        params: dict = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "newOrderRespType": "RESULT",  # ensures executedQty & avgPrice
        }

        if order_type.upper() == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders")
            params["price"] = price
            params["timeInForce"] = "GTC"

        return self._request("POST", endpoint, signed=True, params=params)
