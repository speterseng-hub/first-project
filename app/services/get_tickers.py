# app/services/get_tickers.py
import io
import os, logging
import pandas as pd
from utils.bq import get_client, insert_rows
from datetime import datetime, timezone
import requests

def run():
    PROJECT = os.environ.get("PROJECT_ID")
    RAW_DS = os.environ.get("RAW_DS")
    TICKERS_TABLE = os.environ.get("TICKERS_TABLE")
    TABLE_ID = f"{PROJECT}.{RAW_DS}.{TICKERS_TABLE}"

    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
        response.raise_for_status()

        df = pd.read_html(io.StringIO(response.text))[0]
        df = df.rename(columns=lambda c: c.replace("-", "_").replace(" ", "_").strip())
        df = df.rename(columns={"Symbol": "Ticker"})
        df["Updated"] = datetime.now(timezone.utc).isoformat()
        rows = df.to_dict(orient="records")

        # Truncate then reload — list is ~500 rows, changes quarterly
        get_client().query(f"TRUNCATE TABLE `{TABLE_ID}`").result()

        inserted = insert_rows(TABLE_ID, rows)
        return {"status": "ok", "rows": inserted}

    except Exception as e:
        logging.exception("get_tickers failed")
        return {"status": "error", "error": str(e)}
