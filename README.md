# Webot US Open API

Official API documentation for the Webot US cryptocurrency exchange.

## Documentation

- [webot-openapi.md](./webot-openapi.md) — Full API reference covering public market data and private trading endpoints.

## Overview

| | |
|---|---|
| Base URL | `https://api.webot.com` |
| Protocol | HTTPS |
| Data Format | JSON |
| Authentication | HMAC SHA256 signature |

### Public Endpoints (no authentication required)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/common/symbols` | Trading pair information |
| `GET /api/v1/market/trades` | Recent trades |
| `GET /api/v1/market/depth` | Order book depth |
| `GET /api/v1/market/tickers` | 24-hour ticker statistics |
| `GET /api/v1/market/klines` | Kline / candlestick data |

### Private Endpoints (authentication required)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/account/balances` | Account balances |
| `POST /api/v1/trade/order` | Place new order |
| `GET /api/v1/trade/order` | Get order details |
| `DELETE /api/v1/trade/order` | Cancel order |
| `POST /api/v1/trade/massOrder` | Place multiple orders |
| `GET /api/v1/trade/orderByClientOrderId` | Get order by client order ID |
| `GET /api/v1/trade/openOrders` | Get open orders |
| `GET /api/v1/trade/allOrders` | Get all orders |
| `DELETE /api/v1/trade/allOrders` | Cancel all orders |
| `GET /api/v1/trade/fills` | Get trade fills |
| `GET /api/v1/trade/fillsByOrderId` | Get fills by order ID |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

Apply for an API Key at: https://www.pionex.us/en-US/my-account/api

> **Note:** You need to contact the official team to enable API whitelist access before you can create an API Key.

```bash
cp .env.example .env
```

Edit `.env` and fill in your API Key and Secret:

```
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
```

### 3. Run the test script

```bash
python3 test_openapi.py
```

The script tests all public endpoints (no auth) and private endpoints (HMAC SHA256 signed), and prints a summary at the end.
