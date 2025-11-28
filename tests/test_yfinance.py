from src.data_fetch.yfinance_data import fetch_stock_data

df = fetch_stock_data("FALABELLA.SN")
print(df.head())
