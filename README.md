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
