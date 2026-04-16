# Webot Open API Documentation

## General Information

| Item | Description |
|------|-------------|
| Base URL | `https://api.webot.com` |
| Protocol | HTTPS |
| Data Format | JSON |

### Rate Limits

- All endpoints share a **10 requests/second** limit based on IP.
- Private endpoints share a **10 requests/second** limit based on account.
- Exceeding the limit results in HTTP 429 status code with a 60-second ban.

### Request Format

- **GET requests:** Parameters are passed in the query string.
- **POST/DELETE requests:** Parameters are passed in the request body as JSON (`application/json`).
- Private requests require the `timestamp` query parameter (millisecond Unix timestamp, valid within +/- 20 seconds).
- Private requests require `PIONEX-KEY` and `PIONEX-SIGNATURE` headers.

### Response Format

**Success Response:**

```json
{
  "result": true,
  "data": { ... },
  "timestamp": 1775045161359
}
```

**Error Response:**

```json
{
  "result": false,
  "code": "MARKET_PARAMETER_ERROR",
  "message": "interval param error",
  "timestamp": 1775045161359
}
```

> **Data Type Notes:**
> - All price, quantity, and amount fields are returned as **strings** to preserve precision.
> - All timestamps are **millisecond-level** Unix timestamps.

---

## Authentication

Private endpoints (Account, Trade) require HMAC SHA256 signature authentication. Public endpoints (Common, Market) do not require signing.

### Required Headers

| Header | Description |
|--------|-------------|
| `PIONEX-KEY` | Your API Key |
| `PIONEX-SIGNATURE` | HMAC SHA256 hex signature |

### Required Query Parameter

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds (valid within +/- 20 seconds) |

### Signature Construction

1. Obtain current timestamp in milliseconds.
2. Format query parameters as key-value pairs (no URL encoding for signature values).
3. Sort parameters alphabetically by key and join with `&` (include `timestamp`).
4. Build `PATH_URL` by appending sorted parameters to the request path with `?`.
5. Prepend the HTTP method (`GET`, `POST`, `DELETE`) to the `PATH_URL`.
6. For POST/DELETE requests, append the JSON request body; skip for GET.
7. Generate HMAC SHA256 using your API Secret and the concatenated string, convert to hexadecimal.

**Signature string format:**

- GET: `METHOD + PATH_URL + QUERY + TIMESTAMP`
- POST/DELETE: `METHOD + PATH_URL + QUERY + TIMESTAMP + body`

### API Key Permissions

Each API Key can be configured with **Enable reading** and/or **Enable trading** permissions.

**Endpoints requiring `Enable reading` permission:**
- `GET /api/v1/account/balances`
- `GET /api/v1/trade/order`
- `GET /api/v1/trade/orderByClientOrderId`
- `GET /api/v1/trade/openOrders`
- `GET /api/v1/trade/allOrders`
- `GET /api/v1/trade/fills`
- `GET /api/v1/trade/fillsByOrderId`

**Endpoints requiring `Enable trading` permission:**
- `POST /api/v1/trade/order`
- `DELETE /api/v1/trade/order`
- `POST /api/v1/trade/massOrder`
- `DELETE /api/v1/trade/allOrders`

---

## Error Codes

| Error Code | Description |
|------------|-------------|
| APIKEY_LOST | API Key is missing |
| SIGNATURE_LOST | Signature is missing |
| IP_NOT_WHITELISTED | IP is not in the whitelist |
| INVALID_APIKEY | Invalid API Key |
| INVALID_SIGNATURE | Invalid signature |
| APIKEY_EXPIRED | API Key has expired |
| INVALID_TIMESTAMP | Invalid or expired timestamp |
| PERMISSION_DENIED | Permission denied |
| TRADE_INVALID_SYMBOL | Invalid trading pair |
| TRADE_PARAMETER_ERROR | Invalid trade parameters |
| TRADE_OPERATION_DENIED | Trade operation denied |
| TRADE_ORDER_NOT_FOUND | Order not found |
| MARKET_INVALID_SYMBOL | Invalid market symbol |
| MARKET_PARAMETER_ERROR | Invalid market parameters |
| MARKET_INVALID_TIME | Invalid time parameter |

---

## Public Endpoints

### 1. Get Trading Pair Information

Retrieve configuration parameters for all trading pairs, including precision and trading limits.

```
GET /api/v1/common/symbols
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbols | string | No | Specify trading pairs, separated by commas, e.g. `BTC_USDT,ETH_USDT`. Returns all if omitted |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "symbols": [
      {
        "symbol": "BTC_USDT",
        "type": "SPOT",
        "baseCurrency": "BTC",
        "quoteCurrency": "USDT",
        "basePrecision": 6,
        "quotePrecision": 2,
        "amountPrecision": 8,
        "minAmount": "5",
        "minTradeSize": "0.000001",
        "maxTradeSize": "9000",
        "minTradeDumping": "0.000001",
        "maxTradeDumping": "29.33387056",
        "enable": true,
        "buyCeiling": "1.1",
        "sellFloor": "0.9"
      }
    ]
  },
  "timestamp": 1775045161359
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading pair identifier, format: `{BASE}_{QUOTE}` |
| type | string | Market type, currently only `SPOT` is supported |
| baseCurrency | string | Base currency, e.g. `BTC` |
| quoteCurrency | string | Quote currency, e.g. `USDT` |
| basePrecision | integer | Base currency quantity precision (decimal places) |
| quotePrecision | integer | Quote currency price precision (decimal places) |
| amountPrecision | integer | Order amount precision (decimal places) |
| minAmount | string | Minimum order amount (in quote currency) |
| minTradeSize | string | Minimum trade quantity (in base currency) |
| maxTradeSize | string | Maximum trade quantity (in base currency) |
| minTradeDumping | string | Minimum market sell quantity |
| maxTradeDumping | string | Maximum market sell quantity |
| enable | boolean | Whether the trading pair is tradable |
| buyCeiling | string | Buy price ceiling ratio (relative to market price) |
| sellFloor | string | Sell price floor ratio (relative to market price) |

---

### 2. Get Recent Trades

Returns recent trade data for a specified trading pair, sorted by time in descending order.

```
GET /api/v1/market/trades
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| limit | integer | No | Number of records to return, range 10-500, default 100 |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "trades": [
      {
        "symbol": "BTC_USDT",
        "tradeId": "200000000093911760",
        "price": "68562.81",
        "size": "0.000002",
        "side": "SELL",
        "timestamp": 1775045159489
      }
    ]
  },
  "timestamp": 1775045161397
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading pair |
| tradeId | string | Unique trade ID |
| price | string | Trade price |
| size | string | Trade quantity (in base currency) |
| side | string | Taker side: `BUY` or `SELL` |
| timestamp | integer | Trade time (millisecond timestamp) |

---

### 3. Get Order Book Depth

Returns current bid and ask data for a specified trading pair.

```
GET /api/v1/market/depth
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| limit | integer | No | Number of price levels per side, range 1-1000, default 20 |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "bids": [
      ["68522.91", "0.000253"],
      ["68519.73", "0.000129"]
    ],
    "asks": [
      ["68601.03", "0.681716"],
      ["68601.43", "0.098406"]
    ],
    "updateTime": 1775045158752
  },
  "timestamp": 1775045161414
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| bids | array | Bid list, each item is `[price, quantity]`, sorted by price descending |
| asks | array | Ask list, each item is `[price, quantity]`, sorted by price ascending |
| updateTime | integer | Last update time (millisecond timestamp) |

---

### 4. Get 24-Hour Ticker

Returns 24-hour rolling window ticker statistics. Returns all trading pairs if `symbol` is omitted.

```
GET /api/v1/market/tickers
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | No | Trading pair, e.g. `BTC_USDT`. Returns all if omitted |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "tickers": [
      {
        "symbol": "BTC_USDT",
        "time": 1775045161000,
        "open": "66714.03",
        "close": "68562.81",
        "low": "66481.01",
        "high": "69235.29",
        "volume": "11.620750",
        "amount": "789500.34120510",
        "count": 94964
      }
    ]
  },
  "timestamp": 1775045161398
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading pair |
| time | integer | Snapshot time (millisecond timestamp) |
| open | string | 24h opening price |
| close | string | Latest price |
| high | string | 24h highest price |
| low | string | 24h lowest price |
| volume | string | 24h trading volume (in base currency) |
| amount | string | 24h trading amount (in quote currency) |
| count | integer | 24h number of trades |

---

### 5. Get Kline (Candlestick) Data

Returns kline (OHLCV) data for a specified trading pair and time interval, sorted by time in descending order.

```
GET /api/v1/market/klines
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| interval | string | Yes | Kline interval, see available values below |
| endTime | integer | No | End time (millisecond timestamp), returns latest data if omitted |
| limit | integer | No | Number of records to return, range 1-500, default 100 |

**Kline Interval Values:**

| Value | Description |
|-------|-------------|
| 1M | 1 minute |
| 5M | 5 minutes |
| 15M | 15 minutes |
| 30M | 30 minutes |
| 60M | 1 hour |
| 4H | 4 hours |
| 8H | 8 hours |
| 12H | 12 hours |
| 1D | 1 day |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "klines": [
      {
        "time": 1775044800000,
        "open": "68683.42",
        "close": "68562.81",
        "high": "68687.94",
        "low": "68522.91",
        "volume": "0.052653"
      }
    ]
  },
  "timestamp": 1775045161371
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| time | integer | Kline open time (millisecond timestamp) |
| open | string | Opening price |
| close | string | Closing price |
| high | string | Highest price |
| low | string | Lowest price |
| volume | string | Trading volume (in base currency) |

---

## Private Endpoints

> All private endpoints require authentication. See the [Authentication](#authentication) section for details.

### 6. Get Account Balances

Get trading account balances. Excludes bot and earn accounts.

**Permission required:** `Enable reading`

```
GET /api/v1/account/balances
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "balances": [
      {
        "coin": "BTC",
        "free": "0.90000000",
        "frozen": "0.00000000"
      },
      {
        "coin": "USDT",
        "free": "100.00000000",
        "frozen": "900.00000000"
      }
    ]
  },
  "timestamp": 1566691672311
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| coin | string | Cryptocurrency identifier, e.g. `BTC` |
| free | string | Available balance (8 decimal places) |
| frozen | string | Frozen balance (8 decimal places) |

---

### 7. Place New Order

Place a new order.

**Permission required:** `Enable trading`

```
POST /api/v1/trade/order
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds (query string) |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| side | string | Yes | Order direction: `BUY` or `SELL` |
| type | string | Yes | Order type: `LIMIT` or `MARKET` |
| clientOrderId | string | No | Client order ID (alphanumeric and hyphen, max 64 characters) |
| size | string | Conditional | Order quantity. Required for LIMIT orders and MARKET sell orders |
| price | string | Conditional | Order price. Required for LIMIT orders |
| amount | string | Conditional | Order amount. Required for MARKET buy orders |
| IOC | boolean | No | Immediate-or-cancel flag, default `false` |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "orderId": 123456789,
    "clientOrderId": "my-order-001"
  },
  "timestamp": 1566691672311
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| orderId | integer | Unique order identifier |
| clientOrderId | string | Client-provided order identifier |

---

### 8. Get Order

Get order details by order ID.

**Permission required:** `Enable reading`

```
GET /api/v1/trade/order
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |
| orderId | integer | Yes | Order ID |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "orderId": 123456789,
    "symbol": "BTC_USDT",
    "type": "LIMIT",
    "side": "BUY",
    "price": "68000.00",
    "size": "0.001000",
    "amount": "0",
    "filledSize": "0.001000",
    "filledAmount": "68.00000000",
    "fee": "0.00000100",
    "feeCoin": "BTC",
    "status": "CLOSED",
    "IOC": false,
    "clientOrderId": "my-order-001",
    "source": "API",
    "createTime": 1566691672311,
    "updateTime": 1566691682311
  },
  "timestamp": 1566691692311
}
```

**Order Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| orderId | integer | Order ID |
| symbol | string | Trading pair |
| type | string | Order type: `LIMIT` or `MARKET` |
| side | string | Order direction: `BUY` or `SELL` |
| price | string | Order price |
| size | string | Order quantity |
| amount | string | Market buy order amount |
| filledSize | string | Filled quantity |
| filledAmount | string | Filled amount |
| fee | string | Transaction fee |
| feeCoin | string | Fee currency |
| status | string | Order status: `OPEN` or `CLOSED` |
| IOC | boolean | Immediate-or-cancel flag |
| clientOrderId | string | Client order ID |
| source | string | Order source: `MANUAL` or `API` |
| createTime | integer | Create timestamp (milliseconds) |
| updateTime | integer | Update timestamp (milliseconds) |

---

### 9. Cancel Order

Cancel an existing order.

**Permission required:** `Enable trading`

```
DELETE /api/v1/trade/order
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds (query string) |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| orderId | integer | Yes | Order ID to cancel |

**Response Example:**

```json
{
  "result": true,
  "timestamp": 1566691672311
}
```

---

### 10. Place Multiple Orders

Place multiple orders at once (up to 20, LIMIT only).

**Permission required:** `Enable trading`

```
POST /api/v1/trade/massOrder
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds (query string) |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| orders | array | Yes | Collection of orders (up to 20) |

**Order item fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| side | string | Yes | `BUY` or `SELL` |
| type | string | Yes | Only `LIMIT` is supported |
| clientOrderId | string | No | Client order ID (max 64 characters) |
| size | string | Yes | Order quantity |
| price | string | Yes | Order price |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "orderIds": [
      { "orderId": 123456789, "clientOrderId": "order-1" },
      { "orderId": 123456790, "clientOrderId": "order-2" }
    ]
  },
  "timestamp": 1566691672311
}
```

---

### 11. Get Order by Client Order ID

Get order details by client order ID.

**Permission required:** `Enable reading`

```
GET /api/v1/trade/orderByClientOrderId
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |
| clientOrderId | string | Yes | Client order ID |

**Response:** Same as [Get Order](#8-get-order).

---

### 12. Get Open Orders

Get all open orders for a symbol. Maximum 200 open orders per symbol.

**Permission required:** `Enable reading`

```
GET /api/v1/trade/openOrders
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "orders": [ ... ]
  },
  "timestamp": 1566691672311
}
```

**Response Fields:** `orders` is an array of order objects. See [Order Response Fields](#order-response-fields) for field details.

---

### 13. Get All Orders

Get all orders (open and closed) for a symbol.

**Permission required:** `Enable reading`

```
GET /api/v1/trade/allOrders
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| startTime | integer | No | Start time in milliseconds |
| endTime | integer | No | End time in milliseconds |
| limit | integer | No | Number of records, range 1-200, default 50 |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "orders": [ ... ]
  },
  "timestamp": 1566691672311
}
```

**Response Fields:** `orders` is an array of order objects. See [Order Response Fields](#order-response-fields) for field details.

---

### 14. Cancel All Orders

Cancel all open orders for a symbol.

**Permission required:** `Enable trading`

```
DELETE /api/v1/trade/allOrders
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds (query string) |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |

**Response Example:**

```json
{
  "result": true,
  "timestamp": 1566691672311
}
```

---

### 15. Get Fills

Get trade fills for a symbol.

**Permission required:** `Enable reading`

```
GET /api/v1/trade/fills
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |
| symbol | string | Yes | Trading pair, e.g. `BTC_USDT` |
| startTime | integer | No | Start time in milliseconds |
| endTime | integer | No | End time in milliseconds |

**Response Example:**

```json
{
  "result": true,
  "data": {
    "fills": [
      {
        "id": 987654321,
        "orderId": 123456789,
        "symbol": "BTC_USDT",
        "side": "BUY",
        "role": "TAKER",
        "price": "68000.00",
        "size": "0.001000",
        "fee": "0.00000100",
        "feeCoin": "BTC",
        "timestamp": 1566691672311
      }
    ]
  },
  "timestamp": 1566691672311
}
```

**Fill Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Fill ID |
| orderId | integer | Order ID |
| symbol | string | Trading pair |
| side | string | Trade direction: `BUY` or `SELL` |
| role | string | Participant role: `TAKER` or `MAKER` |
| price | string | Fill price |
| size | string | Fill quantity |
| fee | string | Transaction fee |
| feeCoin | string | Fee currency |
| timestamp | integer | Fill timestamp (milliseconds) |

---

### 16. Get Fills by Order ID

Get trade fills for a specific order.

**Permission required:** `Enable reading`

```
GET /api/v1/trade/fillsByOrderId
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| timestamp | integer | Yes | Current time in milliseconds |
| orderId | integer | Yes | Order ID. Returns empty list if not found |
| fromId | integer | No | Return 100 earlier fills before this fill ID. Returns latest fills if unspecified |

**Response:** Same as [Get Fills](#15-get-fills).

---

## Currently Available Trading Pairs

| Trading Pair | Base Currency | Quote Currency | Status |
|-------------|---------------|----------------|--------|
| BTC_USDT | BTC | USDT | Trading |
| ETH_USDT | ETH | USDT | Suspended |
| NACHO_USD | NACHO | USD | Trading |
| NACHO_USDT | NACHO | USDT | Trading |
