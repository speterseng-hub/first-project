# app/services/agg_prices.py
import os, logging
from utils.bq import run_query
from google.cloud import bigquery



def run():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    ANALYTICS_DS = os.environ.get("ANALYTICS_DS")
    PRICES_TABLE = os.environ.get("PRICES_WITH_RETURNS")
    AGG_PRICES_TABLE = os.environ.get("AGG_PRICES_TABLE")
    TICKERS_TABLE=os.environ.get("TICKERS_TABLE")

    #BQ = bigquery.Client(project=PROJECT_ID)
    try:
        sql = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{ANALYTICS_DS}.{AGG_PRICES_TABLE}` AS
        SELECT
          p.Ticker,
          ANY_VALUE(Security) AS Security,
          ARRAY_AGG(Close ORDER BY Date DESC LIMIT 21) AS OneMonthPrices,
          ARRAY_AGG(Close ORDER BY Date DESC LIMIT 63) AS OneQuarterPrices
        FROM `{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}` p
        LEFT JOIN `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}` t ON t.Ticker = p.Ticker
        GROUP BY p.Ticker;
        """
        run_query(sql)
        return {"status":"ok"}
    except Exception as e:
        logging.exception("agg_prices failed")
        return {"status":"error","error":str(e)}
