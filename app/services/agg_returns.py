# app/services/agg_returns.py
import os, logging
from utils.bq import run_query
from google.cloud import bigquery



def run():
    PROJECT_ID = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    ANALYTICS_DS = os.environ.get("ANALYTICS_DS")
    PRICES_TABLE = os.environ.get("PRICES_WITH_RETURNS")
    AGG_RETURNS_TABLE = os.environ.get("AGG_RETURNS_TABLE")
    TICKERS_TABLE=os.environ.get("TICKERS_TABLE")

    #BQ = bigquery.Client(project=PROJECT_ID)
    try:
        sql = f"""
        CREATE OR REPLACE TABLE `{PROJECT_ID}.{ANALYTICS_DS}.{AGG_RETURNS_TABLE}` AS
        WITH numbered AS (
          SELECT
            p.*,
            ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Date DESC) AS rn
          FROM `{PROJECT_ID}.{RAW_DS}.{PRICES_TABLE}` p
          WHERE Return IS NOT NULL
        ),
        agg AS (
          SELECT
            t.Ticker,
            ANY_VALUE(Security) AS Security,
            EXP(SUM(LOG(1+Return))) - 1 AS TotalReturn,
            EXP(SUM(IF(rn <= 3, LOG(1+Return), 0))) - 1 AS OneWeekReturn,
            EXP(SUM(IF(rn <= 19, LOG(1+Return), 0))) - 1 AS OneMonthReturn,
            EXP(SUM(IF(rn <= 61, LOG(1+Return), 0))) - 1 AS OneQuarterReturn,
            EXP(SUM(IF(rn <= 250, LOG(1+Return), 0))) - 1 AS OneYearReturn
          FROM numbered
          LEFT JOIN `{PROJECT_ID}.{RAW_DS}.{TICKERS_TABLE}` t USING(Ticker)
          GROUP BY Ticker
        )
        SELECT * FROM agg;
        """
        run_query(sql)
        return {"status":"ok"}
    except Exception as e:
        logging.exception("agg_returns failed")
        return {"status":"error","error":str(e)}