# app/services/get_daily_prices.py
import os, logging
import pandas as pd
import yfinance as yf
from utils.bq import get_client, insert_rows
from datetime import datetime, timezone

def _get_tickers():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS", "raw")
    TICKERS_TABLE = os.environ.get("TICKERS_TABLE", "Tickers")
    sql = f"SELECT DISTINCT Ticker FROM `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}`"
    return [r["Ticker"] for r in get_client().query(sql).result()]

def _get_max_dates():
    """Returns {ticker: max_date_str} for rows already in BQ."""
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS", "raw")
    PRICES_TABLE = os.environ.get("PRICES_TABLE", "Prices")
    sql = f"""
        SELECT Ticker, FORMAT_DATE('%Y-%m-%d', MAX(Date)) AS MaxDate
        FROM `{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}`
        GROUP BY Ticker
    """
    return {r["Ticker"]: r["MaxDate"] for r in get_client().query(sql).result()}

def run():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS", "raw")
    PRICES_TABLE = os.environ.get("PRICES_TABLE", "Prices")
    TABLE_ID = f"{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}"

    try:
        tickers = _get_tickers()
        max_dates = _get_max_dates()
        rows = []

        for ticker in tickers:
            try:
                if ticker in max_dates:
                    # Fetch only from the day after the last stored date
                    start = pd.Timestamp(max_dates[ticker]) + pd.Timedelta(days=1)
                    df = yf.Ticker(ticker).history(start=start.strftime("%Y-%m-%d"))
                else:
                    # New ticker — fetch 5 years of history
                    df = yf.Ticker(ticker).history(period="5y")

                if df is None or df.empty:
                    continue

                df = df.reset_index()
                for _, r in df.iterrows():
                    rows.append({
                        "Ticker": ticker,
                        "Date": r["Date"].strftime("%Y-%m-%d"),
                        "Open": float(r["Open"]) if not pd.isna(r["Open"]) else None,
                        "High": float(r["High"]) if not pd.isna(r["High"]) else None,
                        "Low": float(r["Low"]) if not pd.isna(r["Low"]) else None,
                        "Close": float(r["Close"]) if not pd.isna(r["Close"]) else None,
                        "Volume": int(r["Volume"]) if not pd.isna(r["Volume"]) else None,
                        "Updated": datetime.now(timezone.utc).isoformat()
                    })
            except Exception:
                logging.exception("failed ticker %s", ticker)
                continue

        if not rows:
            return {"status": "ok", "rows": 0}

        inserted = insert_rows(TABLE_ID, rows)
        return {"status": "ok", "rows": inserted}

    except Exception as e:
        logging.exception("get_daily_prices failed")
        return {"status": "error", "error": str(e)}
