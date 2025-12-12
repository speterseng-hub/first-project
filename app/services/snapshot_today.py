# app/services/snapshot_today.py
import os, logging
from utils.bq import run_query
from google.cloud import bigquery



def run():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    ANALYTICS_DS = os.environ.get("ANALYTICS_DS")
    PRICES_TABLE = os.environ.get("PRICES_WITH_RETURNS")
    TICKERS_TABLE = os.environ.get("TICKERS_TABLE")
    IND_TABLE = os.environ.get("IND_TABLE")
    SNAPSHOT_TABLE = os.environ.get("TODAY_SNAPSHOT_TABLE")

    try:
        sql = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{ANALYTICS_DS}.{SNAPSHOT_TABLE}` AS
        WITH latest AS (
          SELECT *, ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Date DESC) rn
          FROM `{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}`
        )
        SELECT
          l.Ticker, l.Date, l.Open, l.High, l.Low, l.Close, l.Volume, l.Return,
          t.* EXCEPT(Ticker,Updated),
          i.High_52W, i.Low_52W, i.ATR, i.KCUpper, i.KCLower,
          ((l.Close - i.Low_52W) / NULLIF(i.High_52W - i.Low_52W,0)) * 100 AS C52W_Range,
          ((l.Close - i.KCLower) / NULLIF(i.KCUpper - i.KCLower,0)) * 100 AS KCPos,
          CURRENT_TIMESTAMP() AS Updated
        FROM latest l
        LEFT JOIN `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}` t ON t.Ticker = l.Ticker
        LEFT JOIN `{PROJECT_ID}.{RAW_DS}.{IND_TABLE}` i ON i.Ticker = l.Ticker AND i.Date = l.Date
        WHERE l.rn = 1;
        """
        run_query(sql)
        return {"status":"ok"}
    except Exception as e:
        logging.exception("snapshot_today failed")
        return {"status":"error","error":str(e)}
