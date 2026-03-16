# app/services/get_tickers.py
import io
import os, logging
import pandas as pd
from utils.bq import get_client
from google.cloud import bigquery
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

        # Load job with WRITE_TRUNCATE — atomically replaces table,
        # avoids streaming buffer duplication from TRUNCATE + insert_rows
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = get_client().load_table_from_dataframe(df, TABLE_ID, job_config=job_config)
        job.result()

        return {"status": "ok", "rows": len(df)}

    except Exception as e:
        logging.exception("get_tickers failed")
        return {"status": "error", "error": str(e)}
