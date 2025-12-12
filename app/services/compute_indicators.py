# app/services/compute_indicators.py
import os, logging
from utils.bq import run_query
from google.cloud import bigquery

def run():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS", "raw")
    PRICES_TABLE = os.environ.get("PRICES_WITH_RETURNS", "Prices_with_returns")
    IND_TABLE = os.environ.get("IND_TABLE", "Indicators")
    #BQ = bigquery.Client(PROJECT_ID=PROJECT_ID)
    try:
        sql = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{RAW_DS}.{IND_TABLE}` AS
        WITH tr AS (
          SELECT
            *,
            GREATEST(High - Low,
                     ABS(High - LAG(Close) OVER (PARTITION BY Ticker ORDER BY Date)),
                     ABS(Low  - LAG(Close) OVER (PARTITION BY Ticker ORDER BY Date))
                    ) AS TrueRange
          FROM `{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}`
        ),
        atr AS (
          SELECT
            *,
            MAX(Close) OVER (PARTITION BY Ticker ORDER BY Date ROWS BETWEEN 250 PRECEDING AND CURRENT ROW) AS High_52W,
            MIN(Close) OVER (PARTITION BY Ticker ORDER BY Date ROWS BETWEEN 250 PRECEDING AND CURRENT ROW) AS Low_52W,
            AVG(TrueRange) OVER (PARTITION BY Ticker ORDER BY Date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS ATR
          FROM tr
        )
        SELECT
          Ticker, Date, Close, High_52W, Low_52W, atr.ATR,
          Close + 2 * atr.ATR AS KCUpper,
          Close - 2 * atr.ATR AS KCLower,
          CURRENT_TIMESTAMP() AS Updated
        FROM atr;
        """
        run_query(sql)
        return {"status":"ok"}
    except Exception as e:
        logging.exception("compute_indicators failed")
        return {"status":"error","error":str(e)}
