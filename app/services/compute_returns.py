# app/services/compute_returns.py
import os, logging
from utils.bq import run_query
from google.cloud import bigquery

def run():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    PRICES_TABLE = os.environ.get("PRICES_TABLE")
    OUT_TABLE = os.environ.get("PRICES_WITH_RETURNS")
    #BQ = bigquery.Client(project=PROJECT_ID)
    try:
        sql = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{RAW_DS}.{OUT_TABLE}` AS
        WITH t AS (
          SELECT
            *,
            LAG(Close) OVER (PARTITION BY Ticker ORDER BY Date) AS PrevClose
          FROM `{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}`
        )
        SELECT
          Ticker, Date, Open, High, Low, Close, Volume, Updated,
          SAFE_DIVIDE(Close - PrevClose, PrevClose) AS Return
        FROM t;
        """
        run_query(sql)
        return {"status":"ok"}
    except Exception as e:
        logging.exception("compute_returns failed")
        return {"status":"error","error":str(e)}
