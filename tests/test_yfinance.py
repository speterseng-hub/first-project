
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.data_fetch.yfinance_data import fetch_stock_data

df = fetch_stock_data("FALABELLA.SN")
print(df.head())
