# app/services/get_daily_prices.py
import os, logging
import pandas as pd
import yfinance as yf
from utils.bq import insert_rows, run_query
from datetime import datetime, timezone
from google.cloud import bigquery


def _get_tickers():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS", "raw")
    TICKERS_TABLE = os.environ.get("TICKERS_TABLE", "tickers")
    BQ = bigquery.Client(project=PROJECT_ID)


    sql = f"SELECT DISTINCT Symbol FROM `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}`"
    res = BQ.query(sql).result()
    return [r["Symbol"] for r in res]

def run():
    try:
        PROJECT_ID = os.environ.get("PROJECT_ID")
        RAW_DS = os.environ.get("RAW_DS", "raw")
        PRICES_TABLE = os.environ.get("PRICES_TABLE", "prices")
        tickers = _get_tickers()
        rows = []
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                df = t.history(period="2d")
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
            return {"status":"ok","rows":0}
        TABLE_ID = f"{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}"
        inserted = insert_rows(TABLE_ID, rows)
        return {"status":"ok","rows": inserted}
    except Exception as e:
        logging.exception("get_daily_prices failed")
        return {"status":"error","error":str(e)}