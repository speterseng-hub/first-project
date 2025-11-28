import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Local cache directory
DATA_DIR = os.path.join("data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_stock_data(ticker: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetches historical stock data from Yahoo Finance and caches it locally.
    
    Args:
        ticker (str): Ticker symbol, e.g. 'FALABELLA.SN'
        period (str): Data range ('1y', '5y', 'max', etc.)
        interval (str): Candle frequency ('1d', '1wk', '1mo', etc.)
    
    Returns:
        pd.DataFrame: OHLCV time series
    """
    filename = f"{ticker.replace('.', '_')}.csv"
    filepath = os.path.join(DATA_DIR, filename)

    # If cached file exists, load it
    if os.path.exists(filepath):
        return pd.read_csv(filepath, parse_dates=["Date"], index_col="Date")

    # Fetch from Yahoo Finance
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    # Save to local cache
    df.to_csv(filepath)

    return df

def fetch_multiple(tickers: list, period: str = "5y", interval: str = "1d") -> dict:
    """
    Fetches multiple tickers at once and returns a dict of DataFrames.
    """
    return {ticker: fetch_stock_data(ticker, period, interval) for ticker in tickers}
