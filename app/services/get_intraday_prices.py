# app/services/get_intraday_prices.py
import os, logging
import yfinance as yf
import pandas as pd
from utils.bq import get_client, insert_rows
from datetime import datetime, timezone

def _get_tickers(limit=50):
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    TICKERS_TABLE = os.environ.get("TICKERS_TABLE")
    sql = f"SELECT DISTINCT Ticker FROM `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}` LIMIT {limit}"
    return [r["Ticker"] for r in get_client().query(sql).result()]

def _get_max_datetimes():
    """Returns {ticker: max_datetime_str} for rows already in BQ."""
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    INTRADAY_TABLE = os.environ.get("INTRADAY_TABLE")
    sql = f"""
        SELECT Ticker, MAX(Datetime) AS MaxDatetime
        FROM `{PROJECT_ID}.{RAW_DS}.{INTRADAY_TABLE}`
        GROUP BY Ticker
    """
    return {r["Ticker"]: r["MaxDatetime"] for r in get_client().query(sql).result()}

def run(interval: str = "5m", period: str = "7d"):
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    INTRADAY_TABLE = os.environ.get("INTRADAY_TABLE")
    TABLE_ID = f"{PROJECT_ID}.{RAW_DS}.{INTRADAY_TABLE}"

    try:
        tickers = _get_tickers()
        max_datetimes = _get_max_datetimes()
        rows = []

        for ticker in tickers:
            try:
                df = yf.download(ticker, period=period, interval=interval, progress=False)

                if df is None or df.empty:
                    continue

                df = df.reset_index()

                # Flatten MultiIndex columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] for c in df.columns]

                for _, r in df.iterrows():
                    dt = r["Datetime"].isoformat() if hasattr(r["Datetime"], "isoformat") else str(r["Datetime"])

                    # Skip rows already in BQ
                    if ticker in max_datetimes and dt <= max_datetimes[ticker].isoformat():
                        continue

                    rows.append({
                        "Ticker": ticker,
                        "Datetime": dt,
                        "Open": float(r["Open"]),
                        "High": float(r["High"]),
                        "Low": float(r["Low"]),
                        "Close": float(r["Close"]),
                        "Volume": int(r["Volume"]),
                        "Updated": datetime.now(timezone.utc).isoformat()
                    })

            except Exception:
                logging.exception("intraday fail %s", ticker)
                continue

        if not rows:
            return {"status": "ok", "rows": 0}

        inserted = insert_rows(TABLE_ID, rows)
        return {"status": "ok", "rows": inserted}

    except Exception as e:
        logging.exception("get_intraday_prices failed")
        return {"status": "error", "error": str(e)}
