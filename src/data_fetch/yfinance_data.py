from io import StringIO
import os
from pathlib import Path
from typing import Dict, List, Union
import requests
import pandas as pd
import yfinance as yf

# =========================================================
# Configuration
# =========================================================
DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_sp500_tickers() -> list[str]:
    # Wikipedia blocks requests unless we specify a user-agent
    headers = {"User-Agent": "Mozilla/5.0"}  # avoids 403
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = StringIO(response.text)
    df = pd.read_html(html)[0]

    return df["Symbol"].tolist()

# =========================================================
# Single ticker fetcher
# =========================================================
def fetch_stock_data(tickers: list[str],period: str = "5y",interval: str = "1d",refresh: bool = False) -> pd.DataFrame:   
    
    tickers = f"{tickers.replace('.', '_')}.csv" #FIX
    filepath = DATA_DIR / "tickers.csv"

    # ---------------- Cache handling ---------------- #
    if filepath.exists() and not refresh:
        return pd.read_csv(filepath, parse_dates=["Date"], index_col="Date")

    # ---------------- Live download ---------------- #
    df = yf.download(tickers, period, interval, group_by="ticker")
    #df = yf.Ticker(ticker).history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"⚠ No data returned for ticker '{ticker}'")

    df.to_csv(filepath)
    return df

    
# Lista SP500 (puedes ampliarla con tu propia lista)
#tickers_sp = get_sp500_tickers()
#df = fetch_stock_data()




