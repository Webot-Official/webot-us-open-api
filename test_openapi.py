#!/usr/bin/env python3
"""
Webot Open API test script.
Tests public endpoints (no auth) and private endpoints (HMAC SHA256 signing).
"""

import hashlib
import hmac
import json
import os
import sys
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("BASE_URL", "https://api.webot.com")
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")

# Load from .env file if environment variables are not set
if not API_KEY or not API_SECRET:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        API_KEY = os.getenv("API_KEY", "")
        API_SECRET = os.getenv("API_SECRET", "")

if not API_KEY or not API_SECRET:
    print("Error: API_KEY and API_SECRET must be set in .env file or environment variables.")
    print("Copy .env.example to .env and fill in your credentials.")
    sys.exit(1)


def make_signature(method: str, path: str, params: dict, body: str = "") -> str:
    """
    Build HMAC SHA256 signature per the docs:
    1. Sort query params alphabetically by key
    2. Join as key=value with &
    3. Build: METHOD + path + ? + sorted_params
    4. For POST/DELETE, append body
    5. HMAC SHA256 hex
    """
    sorted_params = "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )
    path_url = f"{path}?{sorted_params}"
    sign_str = f"{method}{path_url}"
    if method in ("POST", "DELETE") and body:
        sign_str += body
    signature = hmac.new(
        API_SECRET.encode(), sign_str.encode(), hashlib.sha256
    ).hexdigest()
    return signature


def get_timestamp() -> int:
    return int(time.time() * 1000)


def signed_get(path: str, extra_params: dict = None) -> dict:
    params = {"timestamp": get_timestamp()}
    if extra_params:
        params.update(extra_params)
    sig = make_signature("GET", path, params)
    headers = {
        "PIONEX-KEY": API_KEY,
        "PIONEX-SIGNATURE": sig,
    }
    resp = requests.get(f"{BASE_URL}{path}", params=params, headers=headers, verify=False)
    return resp.status_code, resp.json()


def signed_post(path: str, body: dict, extra_params: dict = None) -> dict:
    params = {"timestamp": get_timestamp()}
    if extra_params:
        params.update(extra_params)
    body_str = json.dumps(body, separators=(",", ":"))
    sig = make_signature("POST", path, params, body_str)
    headers = {
        "PIONEX-KEY": API_KEY,
        "PIONEX-SIGNATURE": sig,
        "Content-Type": "application/json",
    }
    resp = requests.post(f"{BASE_URL}{path}", params=params, headers=headers, data=body_str, verify=False)
    return resp.status_code, resp.json()


def signed_delete(path: str, body: dict, extra_params: dict = None) -> dict:
    params = {"timestamp": get_timestamp()}
    if extra_params:
        params.update(extra_params)
    body_str = json.dumps(body, separators=(",", ":"))
    sig = make_signature("DELETE", path, params, body_str)
    headers = {
        "PIONEX-KEY": API_KEY,
        "PIONEX-SIGNATURE": sig,
        "Content-Type": "application/json",
    }
    resp = requests.delete(f"{BASE_URL}{path}", params=params, headers=headers, data=body_str, verify=False)
    return resp.status_code, resp.json()


results = []

def print_result(name: str, status: int, data: dict):
    ok = data.get("result", False)
    tag = "PASS" if ok else "FAIL"
    results.append((name, status, ok, data))
    print(f"[{tag}] {name} (HTTP {status})")
    if not ok:
        print(f"  Error: {data.get('code', '')} - {data.get('message', '')}")
        print()
        return
    payload = data.get("data", {})
    for key, val in payload.items():
        if isinstance(val, list):
            print(f"  {key}: ({len(val)} items)")
            for i, item in enumerate(val[:5]):
                if isinstance(item, dict):
                    line = ", ".join(f"{k}={v}" for k, v in item.items())
                    print(f"    [{i}] {line}")
                elif isinstance(item, list):
                    print(f"    [{i}] {item}")
                else:
                    print(f"    [{i}] {item}")
            if len(val) > 5:
                print(f"    ... and {len(val) - 5} more")
        elif isinstance(val, dict):
            line = ", ".join(f"{k}={v}" for k, v in val.items())
            print(f"  {key}: {line}")
        else:
            print(f"  {key}: {val}")
    print()


# ============================================================
# Public Endpoints (no auth required)
# ============================================================

def test_symbols():
    """GET /api/v1/common/symbols"""
    resp = requests.get(f"{BASE_URL}/api/v1/common/symbols", verify=False)
    print_result("Get All Symbols", resp.status_code, resp.json())

    resp = requests.get(f"{BASE_URL}/api/v1/common/symbols", params={"symbols": "BTC_USDT"}, verify=False)
    print_result("Get BTC_USDT Symbol", resp.status_code, resp.json())


def test_trades():
    """GET /api/v1/market/trades"""
    resp = requests.get(f"{BASE_URL}/api/v1/market/trades", params={"symbol": "BTC_USDT", "limit": 10}, verify=False)
    print_result("Get Recent Trades (BTC_USDT, limit=10)", resp.status_code, resp.json())


def test_depth():
    """GET /api/v1/market/depth"""
    resp = requests.get(f"{BASE_URL}/api/v1/market/depth", params={"symbol": "BTC_USDT", "limit": 5}, verify=False)
    print_result("Get Depth (BTC_USDT, limit=5)", resp.status_code, resp.json())


def test_tickers():
    """GET /api/v1/market/tickers"""
    resp = requests.get(f"{BASE_URL}/api/v1/market/tickers", params={"symbol": "BTC_USDT"}, verify=False)
    print_result("Get Ticker (BTC_USDT)", resp.status_code, resp.json())

    resp = requests.get(f"{BASE_URL}/api/v1/market/tickers", verify=False)
    print_result("Get All Tickers", resp.status_code, resp.json())


def test_klines():
    """GET /api/v1/market/klines"""
    resp = requests.get(f"{BASE_URL}/api/v1/market/klines", params={
        "symbol": "BTC_USDT",
        "interval": "1D",
        "limit": 5,
    }, verify=False)
    print_result("Get Klines (BTC_USDT, 1D, limit=5)", resp.status_code, resp.json())


# ============================================================
# Private Endpoints (auth required)
# ============================================================

def test_balances():
    """GET /api/v1/account/balances"""
    status, data = signed_get("/api/v1/account/balances")
    print_result("Get Account Balances", status, data)


def test_open_orders():
    """GET /api/v1/trade/openOrders"""
    status, data = signed_get("/api/v1/trade/openOrders", {"symbol": "BTC_USDT"})
    print_result("Get Open Orders (BTC_USDT)", status, data)


def test_all_orders():
    """GET /api/v1/trade/allOrders"""
    status, data = signed_get("/api/v1/trade/allOrders", {"symbol": "BTC_USDT", "limit": "5"})
    print_result("Get All Orders (BTC_USDT, limit=5)", status, data)


def test_fills():
    """GET /api/v1/trade/fills"""
    status, data = signed_get("/api/v1/trade/fills", {"symbol": "BTC_USDT"})
    print_result("Get Fills (BTC_USDT)", status, data)


if __name__ == "__main__":
    print("=" * 60)
    print("Webot Open API Verification")
    print("=" * 60)
    print()

    print("--- Public Endpoints ---")
    print()
    test_symbols()
    test_trades()
    test_depth()
    test_tickers()
    test_klines()

    print("--- Private Endpoints (Signed) ---")
    print()
    test_balances()
    test_open_orders()
    test_all_orders()
    test_fills()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(1 for _, _, ok, _ in results if ok)
    failed = sum(1 for _, _, ok, _ in results if not ok)
    for name, status, ok, data in results:
        tag = "PASS" if ok else "FAIL"
        extra = ""
        if not ok:
            extra = f" ({data.get('code', '')}: {data.get('message', '')})"
        print(f"  [{tag}] {name} (HTTP {status}){extra}")
    print()
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
