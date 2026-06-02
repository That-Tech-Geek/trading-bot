import logging

logger = logging.getLogger(__name__)


def validate_symbol(symbol: str) -> bool:
    """Return True if *symbol* looks like a valid trading pair."""
    if not symbol or not isinstance(symbol, str):
        logger.error("Symbol must be a non-empty string")
        return False
    if not symbol.upper().endswith("USDT"):
        logger.warning(
            "Symbol %s does not end with USDT – ensure it is a valid USDT-M pair",
            symbol,
        )
    return True


def validate_side(side: str) -> bool:
    """Return True if *side* is BUY or SELL."""
    if side.upper() not in ("BUY", "SELL"):
        logger.error("Side must be BUY or SELL")
        return False
    return True


def validate_order_type(order_type: str, price_provided: bool) -> bool:
    """Return True if *order_type* is valid (and price is provided for LIMIT)."""
    ot = order_type.upper()
    if ot not in ("MARKET", "LIMIT"):
        logger.error("Order type must be MARKET or LIMIT")
        return False
    if ot == "LIMIT" and not price_provided:
        logger.error("LIMIT order requires a price")
        return False
    return True


def validate_quantity(quantity: float) -> bool:
    """Return True if *quantity* is positive."""
    if quantity <= 0:
        logger.error("Quantity must be positive")
        return False
    return True


def validate_price(price: float) -> bool:
    """Return True if *price* is positive."""
    if price <= 0:
        logger.error("Price must be positive")
        return False
    return True
