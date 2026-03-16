# dashboard/queries.py
import os
import pandas as pd
from utils.bq import get_client

PROJECT    = os.environ.get("PROJECT_ID")
RAW_DS     = os.environ.get("RAW_DS", "raw")
AN_DS      = os.environ.get("ANALYTICS_DS", "analytics")
SNAP       = os.environ.get("TODAY_SNAPSHOT_TABLE", "today_snapshot")
AGG_RET    = os.environ.get("AGG_RETURNS_TABLE", "agg_returns")
PRICES     = os.environ.get("PRICES_TABLE", "prices")
IND        = os.environ.get("IND_TABLE", "Indicators")
TICKERS    = os.environ.get("TICKERS_TABLE", "tickers")

def get_screener() -> pd.DataFrame:
    sql = f"""
        SELECT
            s.Ticker,
            s.Security,
            s.GICS_Sector,
            ROUND(s.Close, 2)           AS Price,
            ROUND(s.Return * 100, 2)    AS DayReturn_pct,
            ROUND(r.OneWeekReturn * 100, 2)    AS OneWeek_pct,
            ROUND(r.OneMonthReturn * 100, 2)   AS OneMonth_pct,
            ROUND(r.OneQuarterReturn * 100, 2) AS OneQuarter_pct,
            ROUND(r.OneYearReturn * 100, 2)    AS OneYear_pct,
            ROUND(s.ATR, 2)             AS ATR,
            ROUND(s.C52W_Range, 1)      AS Position_52W_pct
        FROM `{PROJECT}.{AN_DS}.{SNAP}` s
        LEFT JOIN `{PROJECT}.{AN_DS}.{AGG_RET}` r USING(Ticker)
        ORDER BY s.Ticker
    """
    return get_client().query(sql).to_dataframe()

def get_price_history(ticker: str) -> pd.DataFrame:
    sql = f"""
        SELECT Date, Open, High, Low, Close, Volume
        FROM `{PROJECT}.{RAW_DS}.{PRICES}`
        WHERE Ticker = '{ticker}'
          AND Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
        ORDER BY Date
    """
    return get_client().query(sql).to_dataframe()

def get_indicators(ticker: str) -> pd.DataFrame:
    sql = f"""
        SELECT Date, Close, KCUpper, KCLower, ATR, High_52W, Low_52W
        FROM `{PROJECT}.{RAW_DS}.{IND}`
        WHERE Ticker = '{ticker}'
          AND Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
        ORDER BY Date
    """
    return get_client().query(sql).to_dataframe()

def get_sector_returns() -> pd.DataFrame:
    sql = f"""
        SELECT
            t.GICS_Sector                              AS Sector,
            ROUND(AVG(r.OneWeekReturn) * 100, 2)    AS OneWeek_pct,
            ROUND(AVG(r.OneMonthReturn) * 100, 2)   AS OneMonth_pct,
            ROUND(AVG(r.OneQuarterReturn) * 100, 2) AS OneQuarter_pct,
            ROUND(AVG(r.OneYearReturn) * 100, 2)    AS OneYear_pct
        FROM `{PROJECT}.{AN_DS}.{AGG_RET}` r
        LEFT JOIN `{PROJECT}.{RAW_DS}.{TICKERS}` t USING(Ticker)
        WHERE t.GICS_Sector IS NOT NULL
        GROUP BY t.GICS_Sector
        ORDER BY OneMonth_pct DESC
    """
    return get_client().query(sql).to_dataframe()

def get_tickers_list() -> list:
    sql = f"SELECT DISTINCT Ticker FROM `{PROJECT}.{AN_DS}.{SNAP}` ORDER BY Ticker"
    return [r["Ticker"] for r in get_client().query(sql).result()]
