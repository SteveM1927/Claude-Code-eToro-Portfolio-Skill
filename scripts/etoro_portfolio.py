#!/usr/bin/env python3
"""
eToro Portfolio Fetcher — used by the etoro-stock skill.

Reads credentials from environment variables:
  ETORO_API_KEY   — the public API key (x-api-key header)
  ETORO_USER_KEY  — the user key (x-user-key header)

Usage:
  python3 etoro_portfolio.py

Output: JSON with portfolio snapshot including daily P&L per position.
"""

import os
import sys
import uuid
import json
import requests
from datetime import datetime


BASE_URL = "https://public-api.etoro.com/api/v1"


def hdrs():
    key = os.environ.get("ETORO_API_KEY", "")
    ukey = os.environ.get("ETORO_USER_KEY", "")
    if not key or not ukey:
        print(
            "ERROR: Set ETORO_API_KEY and ETORO_USER_KEY environment variables.\n"
            "Get keys from: eToro web > Settings > Trading > Create New Key\n"
            "(Choose Real environment + Read permission)",
            file=sys.stderr,
        )
        sys.exit(1)
    return {
        "x-api-key": key,
        "x-user-key": ukey,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


def get(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", headers=hdrs(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_portfolio():
    return get("/trading/info/real/pnl")["clientPortfolio"]


def fetch_instruments(ids):
    ids_str = ",".join(str(i) for i in ids)
    data = get("/market-data/instruments", params={"instrumentIds": ids_str})
    # API returns instrumentDisplayDatas list
    items = data.get("instrumentDisplayDatas", data.get("instruments", []))
    return {
        item.get("instrumentID", item.get("instrumentId")): {
            "ticker": item.get("symbolFull", item.get("internalSymbolFull", f"ID:{item.get('instrumentID')}")),
            "name": item.get("instrumentDisplayName", item.get("displayname", "")),
        }
        for item in items
    }


def fetch_closing_prices(ids):
    ids_str = ",".join(str(i) for i in ids)
    items = get(
        "/market-data/instruments/history/closing-price",
        params={"instrumentIds": ids_str},
    )
    result = {}
    raw = items if isinstance(items, list) else items.get("data", items.get("instruments", []))
    for item in raw:
        iid = item.get("instrumentId", item.get("instrumentID"))
        # Try officialClosingPrice first, then nested daily price, then closingPrice
        price = (
            item.get("officialClosingPrice")
            or (item.get("closingPrices") or {}).get("daily", {}).get("price")
            or item.get("closingPrice")
        )
        if iid is not None and price is not None:
            result[iid] = price
    return result


def fetch_current_rates(ids):
    ids_str = ",".join(str(i) for i in ids)
    data = get("/market-data/instruments/rates", params={"instrumentIds": ids_str})
    rates_list = data.get("rates", data if isinstance(data, list) else [])
    return {
        item.get("instrumentId", item.get("instrumentID")): item.get("ask", item.get("rate", 0))
        for item in rates_list
    }


def build_snapshot():
    portfolio = fetch_portfolio()
    positions = portfolio.get("positions", [])

    if not positions:
        return {
            "positions": [],
            "total_unrealized_pnl": 0,
            "total_daily_pnl": 0,
            "total_daily_pnl_pct": 0,
            "cash_balance": portfolio.get("credit", 0),
            "as_of": datetime.now().isoformat(),
            "error": None,
        }

    instrument_ids = list({p["instrumentID"] for p in positions})
    instruments = fetch_instruments(instrument_ids)
    prev_closes = fetch_closing_prices(instrument_ids)
    current_rates = fetch_current_rates(instrument_ids)

    results = []
    total_daily_pnl = 0.0
    total_portfolio_value = 0.0

    for pos in positions:
        iid = pos["instrumentID"]
        info = instruments.get(iid, {})
        ticker = info.get("ticker", f"ID:{iid}")
        name = info.get("name", ticker)
        units = pos.get("units", 0)
        open_rate = pos.get("openRate", 0)
        is_buy = pos.get("isBuy", True)

        # Current rate comes from the nested unrealizedPnL block or rates endpoint
        pnl_block = pos.get("unrealizedPnL", {})
        current = pnl_block.get("closeRate") or current_rates.get(iid, open_rate)
        current_value = pnl_block.get("exposureInAccountCurrency") or (units * current)

        prev_close = prev_closes.get(iid, open_rate)
        direction = 1 if is_buy else -1
        daily_pnl = (current - prev_close) * units * direction
        daily_pnl_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0

        unrealized_pnl = pnl_block.get("pnL", pos.get("pnL", 0))

        total_daily_pnl += daily_pnl
        total_portfolio_value += current_value

        results.append(
            {
                "ticker": ticker,
                "name": name,
                "units": round(units, 6),
                "open_rate": round(open_rate, 4),
                "current_rate": round(current, 4),
                "current_value": round(current_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "daily_pnl": round(daily_pnl, 2),
                "daily_pnl_pct": round(daily_pnl_pct, 2),
                "is_buy": is_buy,
            }
        )

    # Sort by absolute daily impact descending
    results.sort(key=lambda x: abs(x["daily_pnl"]), reverse=True)

    total_daily_pnl_pct = (
        (total_daily_pnl / (total_portfolio_value - total_daily_pnl) * 100)
        if (total_portfolio_value - total_daily_pnl)
        else 0
    )

    total_unrealized = sum(p["unrealized_pnl"] for p in results)

    return {
        "positions": results,
        "total_unrealized_pnl": round(total_unrealized, 2),
        "total_daily_pnl": round(total_daily_pnl, 2),
        "total_daily_pnl_pct": round(total_daily_pnl_pct, 2),
        "total_portfolio_value": round(total_portfolio_value, 2),
        "cash_balance": round(portfolio.get("credit", 0), 2),
        "as_of": datetime.now().strftime("%b %d %H:%M"),
        "error": None,
    }


if __name__ == "__main__":
    try:
        snapshot = build_snapshot()
        print(json.dumps(snapshot, indent=2))
    except requests.HTTPError as e:
        print(json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
