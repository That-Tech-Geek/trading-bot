# Trading Bot – Binance Futures Testnet

A Python CLI tool to place **MARKET** and **LIMIT** orders on [Binance Futures Testnet](https://testnet.binancefuture.com/) (USDT-M perpetual contracts).

## Project Structure

```
trading-bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance Futures API client wrapper
│   ├── orders.py            # Order placement logic + validation orchestration
│   ├── validators.py        # Input validation helpers
│   └── logging_config.py    # Logging setup (file + console)
├── logs/
│   ├── market_order.log     # Sample MARKET order log
│   └── limit_order.log      # Sample LIMIT order log
├── cli.py                   # CLI entry point (argparse)
├── requirements.txt         # Python dependencies
├── .env.example             # Template for API credentials
└── README.md                # This file
```

## Setup

### 1. Create a Binance Futures Testnet account

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Register (or log in with GitHub) and generate **API credentials** (API Key + Secret Key)
3. **Important:** Ensure the API key has **Enable Futures** permission

### 2. Clone this repository

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading-bot
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
BINANCE_TESTNET_API_KEY=your_api_key_here
BINANCE_TESTNET_SECRET_KEY=your_secret_key_here
```

## Usage

### Place a MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a LIMIT order (price required)

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000
```

### CLI Arguments

| Argument     | Required   | Description                            |
| ------------ | ---------- | -------------------------------------- |
| `--symbol`   | Yes        | Trading pair (e.g., `BTCUSDT`)         |
| `--side`     | Yes        | `BUY` or `SELL`                        |
| `--type`     | Yes        | `MARKET` or `LIMIT`                    |
| `--quantity` | Yes        | Amount of base asset (e.g., BTC)       |
| `--price`    | For LIMIT  | Price in USDT (required for LIMIT)     |

## Output Example

**MARKET order:**

```
--- Order Request Summary ---
Symbol   : BTCUSDT
Side     : BUY
Type     : MARKET
Quantity : 0.001
----------------------------

--- Order Response ---
Order ID      : 123456789
Status        : FILLED
Executed Qty  : 0.001000
Avg Price     : 49850.25
----------------------
SUCCESS: Order placed successfully.
```

## Logging

All API requests, responses, and errors are logged to `logs/trading_bot.log`.

- **File handler:** `DEBUG` level (captures everything)
- **Console handler:** `INFO` level (user-friendly output)

Sample log files for a MARKET and a LIMIT order are included in the `logs/` directory.

## Assumptions

- The testnet account has sufficient **USDT balance** to fill orders.
- Quantity values respect the exchange's minimum notional and step-size rules (no client-side step-size validation is performed).
- Only **USDT-M perpetual futures** are supported (symbols ending with `USDT`).
- LIMIT orders use `timeInForce: GTC` (Good Till Cancelled).
- API keys have **futures trading** permissions enabled on the testnet.
- The `newOrderRespType` is set to `RESULT` so that `executedQty` and `avgPrice` are returned in the response.

## Error Handling

The application handles:

| Error Type                | Handling                                                   |
| ------------------------- | ---------------------------------------------------------- |
| Missing/invalid arguments | `argparse` rejects before any API call                     |
| Invalid input values      | Validators raise `ValueError` with descriptive messages    |
| Network failures          | `requests` exceptions are caught, logged, and re-raised    |
| API errors (4xx/5xx)      | HTTP status + error body are logged; `raise_for_status()`  |
| Missing API credentials   | Prints an error message and exits with code 1              |

All errors are logged to the log file and displayed to the user with a clear `FAILURE:` message.

## Libraries Used

| Library        | Version   | Purpose                  |
| -------------- | --------- | ------------------------ |
| `requests`     | ≥2.32.4   | HTTP client for REST API |
| `python-dotenv`| 1.2.2     | Load `.env` credentials  |
