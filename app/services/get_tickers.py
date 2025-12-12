# app/services/get_tickers.py
import os, logging
import pandas as pd
from utils.bq import insert_rows
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

        # Añadimos un User-Agent para evitar el 403
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza error si falla la descarga

        # pd.read_html puede leer desde un string HTML
        tables = pd.read_html(response.text)
        df = tables[0]
        df["Updated"] = datetime.now(timezone.utc).isoformat()
        df = df.rename(columns=lambda c: c.replace("-", "_").replace(" ","_").strip())
        df = df.rename(columns={'Symbol':'Ticker'})
        rows = df.to_dict(orient="records")
        inserted = insert_rows(TABLE_ID, rows)
        return {"status":"ok","rows": inserted}
    
    except Exception as e:
        logging.exception("get_tickers failed")
        return {"status":"error","error": str(e),"sample":next(iter(rows))} # outputs 'foo'}
