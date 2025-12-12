# app/services/get_intraday_prices.py
import os, logging
import yfinance as yf
import pandas as pd
from utils.bq import insert_rows
from google.cloud import bigquery
from datetime import datetime,timezone



def _get_tickers(limit=50):
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    TICKERS_TABLE = os.environ.get("TICKERS_TABLE")
    BQ = bigquery.Client(project=PROJECT_ID)
    sql = f"""  SELECT DISTINCT Ticker 
                    FROM `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}` 
                LIMIT {limit}"""
    res = BQ.query(sql).result()
    return [r["Ticker"] for r in res]

def run(interval: str = "5m", period: str = "7d"):
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    INTRADAY_TABLE = os.environ.get("INTRADAY_TABLE")
    TABLE_ID = f"{PROJECT_ID}.{RAW_DS}.{INTRADAY_TABLE}"
    try:
        tickers = _get_tickers()
        rows = []
        for ticker in tickers:
            try:
                df = yf.download(ticker, period=period, 
                                 interval=interval, progress=True)

                if df is None or df.empty:
                    continue

                df = df.reset_index()

                # Aplanar columnas si tienen MultiIndex
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] for c in df.columns]

                for _, r in df.iterrows():
                    rows.append({
                        "Ticker": ticker,
                        "Datetime": r["Datetime"].isoformat() 
                            if hasattr(r["Datetime"], "isoformat") 
                            else str(r["Datetime"]),
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
            return {"status":"ok","rows":0}
        inserted = insert_rows(TABLE_ID, rows)
        return {"status":"ok","rows":inserted}
    except Exception as e:
        logging.exception("get_intraday_prices failed")
        return {"status":"error","error":str(e)}
