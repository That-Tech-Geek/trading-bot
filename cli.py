#!/usr/bin/env python3
"""CLI entry-point for the Binance Futures Testnet trading bot."""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.orders import place_order
from bot.logging_config import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="Place orders on Binance Futures Testnet"
    )
    parser.add_argument(
        "--symbol", required=True, help="Trading pair, e.g. BTCUSDT"
    )
    parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], help="Order side"
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["MARKET", "LIMIT"],
        help="Order type",
    )
    parser.add_argument(
        "--quantity", required=True, type=float, help="Order quantity"
    )
    parser.add_argument(
        "--price", type=float, help="Price for LIMIT orders"
    )

    args = parser.parse_args()

    load_dotenv()

    api_key = os.getenv("BINANCE_TESTNET_API_KEY")
    api_secret = os.getenv("BINANCE_TESTNET_SECRET_KEY")

    if not api_key or not api_secret:
        print(
            "ERROR: Please set BINANCE_TESTNET_API_KEY and "
            "BINANCE_TESTNET_SECRET_KEY environment variables (or add them to .env)"
        )
        sys.exit(1)

    os.makedirs("logs", exist_ok=True)
    setup_logging("logs/trading_bot.log")

    print("\n--- Order Request Summary ---")
    print(f"Symbol   : {args.symbol.upper()}")
    print(f"Side     : {args.side.upper()}")
    print(f"Type     : {args.type.upper()}")
    print(f"Quantity : {args.quantity}")
    if args.price:
        print(f"Price    : {args.price}")
    print("----------------------------\n")

    client = BinanceFuturesClient(api_key, api_secret)

    try:
        response = place_order(
            client, args.symbol, args.side, args.type, args.quantity, args.price
        )

        print("--- Order Response ---")
        print(f"Order ID      : {response.get('orderId')}")
        print(f"Status        : {response.get('status')}")
        print(f"Executed Qty  : {response.get('executedQty')}")
        print(f"Avg Price     : {response.get('avgPrice')}")
        print("----------------------")
        print("SUCCESS: Order placed successfully.\n")

    except Exception as e:
        print(f"FAILURE: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
