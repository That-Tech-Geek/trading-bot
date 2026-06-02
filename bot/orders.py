import logging

from bot.client import BinanceFuturesClient
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
)

logger = logging.getLogger(__name__)


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
) -> dict:
    """Validate inputs and place an order via the Binance client.

    Returns the parsed JSON response from the API on success.
    Raises ``ValueError`` for invalid inputs and re-raises any API / network
    exceptions after logging.
    """
    if not validate_symbol(symbol):
        raise ValueError("Invalid symbol")
    if not validate_side(side):
        raise ValueError("Invalid side")
    if not validate_order_type(order_type, price is not None):
        raise ValueError("Invalid order type or missing price for LIMIT")
    if not validate_quantity(quantity):
        raise ValueError("Invalid quantity")
    if order_type.upper() == "LIMIT" and not validate_price(price):
        raise ValueError("Invalid price")

    logger.info(
        "Placing %s %s order for %s %s%s",
        order_type.upper(),
        side.upper(),
        quantity,
        symbol.upper(),
        f" @ {price}" if price else "",
    )

    try:
        response = client.place_order(symbol, side, order_type, quantity, price)
        logger.info(
            "Order placed successfully. Order ID: %s", response.get("orderId")
        )
        return response
    except Exception as e:
        logger.error("Order placement failed: %s", str(e))
        raise
