#!/usr/bin/env python3
"""Comprehensive test suite for the trading bot.

Tests every code path: validators, client construction, signature generation,
order orchestration, error handling, and (optionally) live API calls.
"""

import hashlib
import hmac
import os
import sys
import logging
from unittest.mock import patch, MagicMock
from urllib.parse import urlencode, parse_qs, urlparse

# ──────────────────────────────────────────────────────────────────────────── #
# Setup
# ──────────────────────────────────────────────────────────────────────────── #
passed = 0
failed = 0
errors = []


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        msg = f"  ❌ {name}" + (f" — {detail}" if detail else "")
        print(msg)
        errors.append(msg)


# ──────────────────────────────────────────────────────────────────────────── #
# 1. VALIDATOR TESTS
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 1. VALIDATORS ═══")

from bot.validators import (
    validate_symbol, validate_side, validate_order_type,
    validate_quantity, validate_price,
)

# validate_symbol
check("symbol: valid BTCUSDT", validate_symbol("BTCUSDT"))
check("symbol: valid lowercase", validate_symbol("ethusdt"))
check("symbol: empty string", not validate_symbol(""))
check("symbol: None", not validate_symbol(None))
check("symbol: non-USDT (warns but valid)", validate_symbol("BTCBUSD"))

# validate_side
check("side: BUY", validate_side("BUY"))
check("side: SELL", validate_side("SELL"))
check("side: lowercase buy", validate_side("buy"))
check("side: invalid HOLD", not validate_side("HOLD"))
check("side: empty", not validate_side(""))

# validate_order_type
check("type: MARKET no price", validate_order_type("MARKET", False))
check("type: MARKET with price", validate_order_type("MARKET", True))
check("type: LIMIT with price", validate_order_type("LIMIT", True))
check("type: LIMIT without price", not validate_order_type("LIMIT", False))
check("type: invalid STOP", not validate_order_type("STOP", True))
check("type: lowercase limit", validate_order_type("limit", True))

# validate_quantity
check("quantity: positive", validate_quantity(0.001))
check("quantity: zero", not validate_quantity(0))
check("quantity: negative", not validate_quantity(-1.5))
check("quantity: large", validate_quantity(999999))

# validate_price
check("price: positive", validate_price(50000))
check("price: zero", not validate_price(0))
check("price: negative", not validate_price(-100))
check("price: fractional", validate_price(0.5))

# ──────────────────────────────────────────────────────────────────────────── #
# 2. CLIENT CONSTRUCTION & SIGNATURE
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 2. CLIENT CONSTRUCTION & SIGNATURE ═══")

from bot.client import BinanceFuturesClient

client = BinanceFuturesClient("test_api_key_abc", "test_api_secret_xyz")

check("client: api_key stored", client.api_key == "test_api_key_abc")
check("client: api_secret stored", client.api_secret == "test_api_secret_xyz")
check("client: session header set", client.session.headers.get("X-MBX-APIKEY") == "test_api_key_abc")
check("client: no Content-Type header", "Content-Type" not in client.session.headers,
      "Content-Type header would break Binance API")
check("client: BASE_URL correct", client.BASE_URL == "https://testnet.binancefuture.com")

# Signature verification — manually compute and compare
test_params = {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.001}
expected_sig = hmac.new(
    b"test_api_secret_xyz",
    urlencode(test_params).encode("utf-8"),
    hashlib.sha256,
).hexdigest()
actual_sig = client._generate_signature(test_params)
check("signature: matches manual HMAC-SHA256", actual_sig == expected_sig,
      f"expected={expected_sig}, got={actual_sig}")

# Signature with different params gives different result
test_params_2 = {"symbol": "ETHUSDT", "side": "SELL", "type": "LIMIT", "quantity": 1.0}
sig2 = client._generate_signature(test_params_2)
check("signature: different params → different sig", actual_sig != sig2)

# ──────────────────────────────────────────────────────────────────────────── #
# 3. ORDER PLACEMENT LOGIC (MOCKED)
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 3. ORDER PLACEMENT (MOCKED API) ═══")

from bot.orders import place_order

# Mock a successful MARKET order response
mock_market_response = {
    "orderId": 12345678,
    "symbol": "BTCUSDT",
    "status": "FILLED",
    "side": "BUY",
    "type": "MARKET",
    "executedQty": "0.001000",
    "avgPrice": "49850.25",
}

with patch.object(client, "place_order", return_value=mock_market_response) as mock_po:
    result = place_order(client, "BTCUSDT", "BUY", "MARKET", 0.001)
    check("market order: returns response", result == mock_market_response)
    check("market order: orderId present", result.get("orderId") == 12345678)
    check("market order: status FILLED", result.get("status") == "FILLED")
    check("market order: executedQty present", result.get("executedQty") == "0.001000")
    check("market order: avgPrice present", result.get("avgPrice") == "49850.25")
    mock_po.assert_called_once_with("BTCUSDT", "BUY", "MARKET", 0.001, None)
    check("market order: client.place_order called correctly", True)

# Mock a successful LIMIT order response
mock_limit_response = {
    "orderId": 12345679,
    "symbol": "BTCUSDT",
    "status": "NEW",
    "side": "SELL",
    "type": "LIMIT",
    "executedQty": "0.000000",
    "avgPrice": "0.00",
    "price": "50000",
    "timeInForce": "GTC",
}

with patch.object(client, "place_order", return_value=mock_limit_response) as mock_po:
    result = place_order(client, "BTCUSDT", "SELL", "LIMIT", 0.001, 50000)
    check("limit order: returns response", result == mock_limit_response)
    check("limit order: status NEW", result.get("status") == "NEW")
    check("limit order: price present", result.get("price") == "50000")
    check("limit order: timeInForce GTC", result.get("timeInForce") == "GTC")
    mock_po.assert_called_once_with("BTCUSDT", "SELL", "LIMIT", 0.001, 50000)
    check("limit order: client.place_order called with price", True)

# ──────────────────────────────────────────────────────────────────────────── #
# 4. ERROR HANDLING
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 4. ERROR HANDLING ═══")

# Invalid symbol
try:
    place_order(client, "", "BUY", "MARKET", 0.001)
    check("error: empty symbol raises", False, "No exception raised")
except ValueError as e:
    check("error: empty symbol raises ValueError", "Invalid symbol" in str(e))

# Invalid side
try:
    place_order(client, "BTCUSDT", "HOLD", "MARKET", 0.001)
    check("error: invalid side raises", False, "No exception raised")
except ValueError as e:
    check("error: invalid side raises ValueError", "Invalid side" in str(e))

# LIMIT without price
try:
    place_order(client, "BTCUSDT", "BUY", "LIMIT", 0.001)
    check("error: LIMIT no price raises", False, "No exception raised")
except ValueError as e:
    check("error: LIMIT no price raises ValueError", "Invalid order type" in str(e))

# Invalid order type
try:
    place_order(client, "BTCUSDT", "BUY", "STOP", 0.001)
    check("error: invalid type raises", False, "No exception raised")
except ValueError as e:
    check("error: invalid type raises ValueError", "Invalid order type" in str(e))

# Zero quantity
try:
    place_order(client, "BTCUSDT", "BUY", "MARKET", 0)
    check("error: zero quantity raises", False, "No exception raised")
except ValueError as e:
    check("error: zero quantity raises ValueError", "Invalid quantity" in str(e))

# Negative quantity
try:
    place_order(client, "BTCUSDT", "BUY", "MARKET", -0.5)
    check("error: negative quantity raises", False, "No exception raised")
except ValueError as e:
    check("error: negative quantity raises ValueError", "Invalid quantity" in str(e))

# LIMIT with zero price
try:
    place_order(client, "BTCUSDT", "BUY", "LIMIT", 0.001, 0)
    check("error: zero price raises", False, "No exception raised")
except ValueError as e:
    check("error: zero price raises ValueError", "Invalid price" in str(e))

# Negative price
try:
    place_order(client, "BTCUSDT", "BUY", "LIMIT", 0.001, -100)
    check("error: negative price raises", False, "No exception raised")
except ValueError as e:
    check("error: negative price raises ValueError", "Invalid price" in str(e))

# API exception propagation
with patch.object(client, "place_order", side_effect=Exception("Connection timeout")):
    try:
        place_order(client, "BTCUSDT", "BUY", "MARKET", 0.001)
        check("error: API exception propagates", False, "No exception raised")
    except Exception as e:
        check("error: API exception propagates", "Connection timeout" in str(e))

# HTTP error propagation
import requests as req
with patch.object(client, "place_order", side_effect=req.exceptions.HTTPError("400 Bad Request")):
    try:
        place_order(client, "BTCUSDT", "BUY", "MARKET", 0.001)
        check("error: HTTP error propagates", False)
    except req.exceptions.HTTPError as e:
        check("error: HTTP error propagates", "400" in str(e))

# ──────────────────────────────────────────────────────────────────────────── #
# 5. CLIENT._REQUEST METHOD (MOCKED HTTP)
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 5. HTTP REQUEST LAYER ═══")

# Test unsigned request
mock_response = MagicMock()
mock_response.status_code = 200
mock_response.json.return_value = {"serverTime": 1234567890}

with patch.object(client.session, "request", return_value=mock_response) as mock_req:
    result = client._request("GET", "/fapi/v1/time", signed=False)
    check("unsigned request: returns JSON", result == {"serverTime": 1234567890})
    call_args = mock_req.call_args
    called_url = call_args[0][1]
    check("unsigned request: correct URL", "testnet.binancefuture.com/fapi/v1/time" in called_url)

# Test signed request — verify signature is appended
with patch.object(client.session, "request", return_value=mock_response) as mock_req:
    result = client._request("POST", "/fapi/v1/order", signed=True,
                              params={"symbol": "BTCUSDT", "side": "BUY"})
    call_args = mock_req.call_args
    called_url = call_args[0][1]
    parsed = urlparse(called_url)
    qs = parse_qs(parsed.query)
    check("signed request: has timestamp", "timestamp" in qs)
    check("signed request: has recvWindow", "recvWindow" in qs)
    check("signed request: has signature", "signature" in qs)
    check("signed request: has symbol param", qs.get("symbol") == ["BTCUSDT"])
    check("signed request: recvWindow is 5000", qs.get("recvWindow") == ["5000"])

# Test error response handling
mock_error_response = MagicMock()
mock_error_response.status_code = 400
mock_error_response.text = '{"code":-1102,"msg":"Mandatory parameter missing"}'
mock_error_response.raise_for_status.side_effect = req.exceptions.HTTPError("400 Bad Request")

with patch.object(client.session, "request", return_value=mock_error_response):
    try:
        client._request("POST", "/fapi/v1/order", signed=True, params={"symbol": "BTCUSDT"})
        check("http error: raise_for_status called", False)
    except req.exceptions.HTTPError:
        check("http error: raise_for_status raises HTTPError", True)

# ──────────────────────────────────────────────────────────────────────────── #
# 6. CLIENT.place_order PARAM BUILDING
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 6. PLACE_ORDER PARAM BUILDING ═══")

# Test MARKET order params
with patch.object(client, "_request", return_value=mock_market_response) as mock_req:
    client.place_order("btcusdt", "buy", "market", 0.001)
    call_args = mock_req.call_args
    params = call_args[1].get("params") or call_args[0][3] if len(call_args[0]) > 3 else call_args[1]["params"]
    check("params: symbol uppercased", params["symbol"] == "BTCUSDT")
    check("params: side uppercased", params["side"] == "BUY")
    check("params: type uppercased", params["type"] == "MARKET")
    check("params: quantity set", params["quantity"] == 0.001)
    check("params: newOrderRespType RESULT", params["newOrderRespType"] == "RESULT")
    check("params: no price for MARKET", "price" not in params)
    check("params: no timeInForce for MARKET", "timeInForce" not in params)

# Test LIMIT order params
with patch.object(client, "_request", return_value=mock_limit_response) as mock_req:
    client.place_order("ethusdt", "sell", "limit", 1.5, 3000.50)
    call_args = mock_req.call_args
    params = call_args[1].get("params") or call_args[0][3] if len(call_args[0]) > 3 else call_args[1]["params"]
    check("limit params: price set", params["price"] == 3000.50)
    check("limit params: timeInForce GTC", params["timeInForce"] == "GTC")
    check("limit params: symbol ETHUSDT", params["symbol"] == "ETHUSDT")

# Test LIMIT order without price raises ValueError in client
try:
    # bypass the order orchestration layer, call client directly
    client_direct = BinanceFuturesClient("key", "secret")
    with patch.object(client_direct, "_request"):
        client_direct.place_order("BTCUSDT", "BUY", "LIMIT", 0.001, None)
        check("client: LIMIT no price raises", False)
except ValueError as e:
    check("client: LIMIT no price raises ValueError", "Price is required" in str(e))

# ──────────────────────────────────────────────────────────────────────────── #
# 7. LOGGING CONFIG
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 7. LOGGING CONFIG ═══")

from bot.logging_config import setup_logging
import tempfile

# Test with a temp file to verify file handler
test_log = os.path.join(os.path.dirname(__file__) or ".", "logs", "_test_verify.log")
test_logger = setup_logging(test_log)
check("logging: returns logger", test_logger is not None)
check("logging: has handlers", len(test_logger.handlers) >= 2)

# Count handler types
file_handlers = [h for h in test_logger.handlers if isinstance(h, logging.FileHandler)]
stream_handlers = [h for h in test_logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
check("logging: has file handler", len(file_handlers) >= 1)
check("logging: has stream handler", len(stream_handlers) >= 1)

# Check levels
for fh in file_handlers:
    if fh.baseFilename.endswith("_test_verify.log"):
        check("logging: file handler DEBUG level", fh.level == logging.DEBUG)
for sh in stream_handlers:
    check("logging: stream handler INFO level", sh.level == logging.INFO)

# Verify it actually writes to file
test_logger.info("TEST_VERIFY_MESSAGE")
for fh in file_handlers:
    fh.flush()
if os.path.exists(test_log):
    with open(test_log) as f:
        content = f.read()
    check("logging: writes to file", "TEST_VERIFY_MESSAGE" in content)
else:
    check("logging: writes to file", False, "Log file not created")

# Clean up handlers BEFORE deleting the file (Windows file-lock)
for h in list(test_logger.handlers):
    if isinstance(h, logging.FileHandler) and h.baseFilename.endswith("_test_verify.log"):
        test_logger.removeHandler(h)
        h.close()

# Now safe to remove
if os.path.exists(test_log):
    os.remove(test_log)

# ──────────────────────────────────────────────────────────────────────────── #
# 8. CLI ARGPARSE (subprocess)
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 8. CLI INTEGRATION ═══")

import subprocess

# --help works
r = subprocess.run([sys.executable, "cli.py", "--help"], capture_output=True, text=True)
check("cli: --help exits 0", r.returncode == 0)
check("cli: --help shows symbol", "--symbol" in r.stdout)
check("cli: --help shows side", "--side" in r.stdout)
check("cli: --help shows type", "--type" in r.stdout)
check("cli: --help shows quantity", "--quantity" in r.stdout)
check("cli: --help shows price", "--price" in r.stdout)

# Missing required args
r = subprocess.run([sys.executable, "cli.py"], capture_output=True, text=True)
check("cli: no args exits non-zero", r.returncode != 0)

# Missing API keys (no .env)
r = subprocess.run(
    [sys.executable, "cli.py", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "0.001"],
    capture_output=True, text=True,
    env={**os.environ, "BINANCE_TESTNET_API_KEY": "", "BINANCE_TESTNET_SECRET_KEY": ""},
)
check("cli: missing keys exits 1", r.returncode == 1)
check("cli: missing keys shows error", "ERROR" in r.stdout or "ERROR" in r.stderr)

# Invalid side rejected by argparse
r = subprocess.run(
    [sys.executable, "cli.py", "--symbol", "BTCUSDT", "--side", "HOLD", "--type", "MARKET", "--quantity", "0.001"],
    capture_output=True, text=True,
)
check("cli: invalid side rejected", r.returncode != 0)
check("cli: invalid side error message", "invalid choice" in r.stderr.lower())

# Invalid type rejected by argparse
r = subprocess.run(
    [sys.executable, "cli.py", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "STOP", "--quantity", "0.001"],
    capture_output=True, text=True,
)
check("cli: invalid type rejected", r.returncode != 0)

# Invalid quantity type
r = subprocess.run(
    [sys.executable, "cli.py", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "abc"],
    capture_output=True, text=True,
)
check("cli: non-numeric quantity rejected", r.returncode != 0)

# ──────────────────────────────────────────────────────────────────────────── #
# 9. LIVE API TEST (if credentials available)
# ──────────────────────────────────────────────────────────────────────────── #
print("\n═══ 9. LIVE API TEST ═══")

from dotenv import load_dotenv
load_dotenv()

live_key = os.getenv("BINANCE_TESTNET_API_KEY")
live_secret = os.getenv("BINANCE_TESTNET_SECRET_KEY")

if live_key and live_secret:
    print("  🔑 Credentials found — testing live API...")
    live_client = BinanceFuturesClient(live_key, live_secret)

    # Test server connectivity (unsigned endpoint)
    try:
        ping = live_client._request("GET", "/fapi/v1/ping")
        check("live: ping successful", ping == {})
    except Exception as e:
        check("live: ping", False, str(e))

    # Test server time
    try:
        st = live_client._request("GET", "/fapi/v1/time")
        check("live: server time", "serverTime" in st)
    except Exception as e:
        check("live: server time", False, str(e))

    # Test MARKET BUY order
    try:
        resp = place_order(live_client, "BTCUSDT", "BUY", "MARKET", 0.001)
        check("live: MARKET BUY orderId", resp.get("orderId") is not None)
        check("live: MARKET BUY status", resp.get("status") in ("FILLED", "NEW", "PARTIALLY_FILLED"))
        check("live: MARKET BUY executedQty", resp.get("executedQty") is not None)
        check("live: MARKET BUY avgPrice", resp.get("avgPrice") is not None)
        print(f"    → Order ID: {resp.get('orderId')}, Status: {resp.get('status')}, "
              f"Qty: {resp.get('executedQty')}, Avg Price: {resp.get('avgPrice')}")
    except Exception as e:
        check("live: MARKET BUY order", False, str(e))

    # Test LIMIT SELL order (far from market to avoid fill)
    try:
        resp = place_order(live_client, "BTCUSDT", "SELL", "LIMIT", 0.001, 999999)
        check("live: LIMIT SELL orderId", resp.get("orderId") is not None)
        check("live: LIMIT SELL status NEW", resp.get("status") == "NEW")
        print(f"    → Order ID: {resp.get('orderId')}, Status: {resp.get('status')}")
    except Exception as e:
        check("live: LIMIT SELL order", False, str(e))
else:
    print("  ⚠️  No credentials — skipping live API tests")
    print("     Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_SECRET_KEY to enable")


# ──────────────────────────────────────────────────────────────────────────── #
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────── #
print(f"\n{'═' * 50}")
print(f"  RESULTS: {passed} passed, {failed} failed")
print(f"{'═' * 50}")

if errors:
    print("\n  FAILURES:")
    for e in errors:
        print(f"  {e}")

sys.exit(1 if failed > 0 else 0)
