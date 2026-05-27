"""
Price Fetcher — yfinance-based live price and FX data.

Fetches:
  - Current price (LTP) for any ticker
  - Daily % change (vs previous close)
  - Monthly % change (~22 trading days)
  - USD/INR and GBP/INR exchange rates

Results are cached in Streamlit (ttl=300s / 5 min) by the caller.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Optional, List


# ── Exchange rate fetching ──────────────────────────────────────────────────────

def get_fx_rates() -> Dict[str, float]:
    """
    Return a dict with current FX rates relative to INR.

    Keys: "USD", "GBP", "INR"
    Falls back to sensible defaults on failure.
    """
    rates = {"INR": 1.0, "USD": 84.0, "GBP": 107.0}
    pairs = {"USD": "USDINR=X", "GBP": "GBPINR=X"}

    for currency, ticker in pairs.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d", interval="1d")
            if not hist.empty:
                rates[currency] = float(hist["Close"].iloc[-1])
        except Exception:
            pass  # keep default

    return rates


# ── Single-ticker price ─────────────────────────────────────────────────────────

def get_price_info(ticker: str) -> Dict:
    """
    Fetch price info for a single ticker.

    Returns dict with keys:
        price             float | None   — latest close
        daily_change_pct  float | None   — % change vs previous day
        monthly_change_pct float | None  — % change vs ~22 trading days ago
        currency          str            — currency reported by yfinance
    """
    result = {
        "price": None,
        "daily_change_pct": None,
        "monthly_change_pct": None,
        "currency": "USD",
    }
    try:
        stock = yf.Ticker(ticker)
        hist  = stock.history(period="35d", interval="1d")

        if hist.empty or len(hist) < 1:
            return result

        closes = hist["Close"].dropna()

        result["price"] = float(closes.iloc[-1])

        if len(closes) >= 2:
            prev  = float(closes.iloc[-2])
            result["daily_change_pct"] = ((result["price"] - prev) / prev) * 100

        if len(closes) >= 22:
            month_ago = float(closes.iloc[-22])
            result["monthly_change_pct"] = ((result["price"] - month_ago) / month_ago) * 100
        elif len(closes) >= 2:
            # Use oldest available if < 22 trading days of history
            oldest = float(closes.iloc[0])
            result["monthly_change_pct"] = ((result["price"] - oldest) / oldest) * 100

        # Grab currency from ticker info
        try:
            info = stock.fast_info
            result["currency"] = getattr(info, "currency", "USD") or "USD"
        except Exception:
            pass

    except Exception:
        pass

    return result


# ── Bulk price fetch ────────────────────────────────────────────────────────────

def get_prices_bulk(tickers: List[str]) -> Dict[str, Dict]:
    """
    Fetch price info for a list of tickers efficiently using yfinance's
    bulk download where possible.

    Returns dict[ticker -> price_info_dict].
    """
    if not tickers:
        return {}

    results: Dict[str, Dict] = {}

    try:
        # Bulk download for speed (35 days of daily data)
        raw = yf.download(
            tickers=tickers,
            period="35d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        # yfinance returns a MultiIndex DataFrame when len(tickers) > 1,
        # or a flat DataFrame when len(tickers) == 1
        if len(tickers) == 1:
            ticker = tickers[0]
            closes = raw["Close"].dropna() if "Close" in raw.columns else pd.Series(dtype=float)
            results[ticker] = _closes_to_info(closes)
        else:
            closes_all = raw["Close"] if "Close" in raw.columns else pd.DataFrame()
            for ticker in tickers:
                if ticker in closes_all.columns:
                    closes = closes_all[ticker].dropna()
                    results[ticker] = _closes_to_info(closes)
                else:
                    results[ticker] = _empty_info()

    except Exception:
        # Fallback to individual fetches if bulk fails
        for ticker in tickers:
            results[ticker] = get_price_info(ticker)

    return results


def _closes_to_info(closes: pd.Series) -> Dict:
    """Convert a Series of closing prices into a price_info dict."""
    info = _empty_info()
    if closes.empty:
        return info

    info["price"] = float(closes.iloc[-1])

    if len(closes) >= 2:
        prev = float(closes.iloc[-2])
        if prev:
            info["daily_change_pct"] = ((info["price"] - prev) / prev) * 100

    if len(closes) >= 22:
        month_ago = float(closes.iloc[-22])
        if month_ago:
            info["monthly_change_pct"] = ((info["price"] - month_ago) / month_ago) * 100
    elif len(closes) >= 2:
        oldest = float(closes.iloc[0])
        if oldest:
            info["monthly_change_pct"] = ((info["price"] - oldest) / oldest) * 100

    return info


def _empty_info() -> Dict:
    return {"price": None, "daily_change_pct": None, "monthly_change_pct": None, "currency": "USD"}
