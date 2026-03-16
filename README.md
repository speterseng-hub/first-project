# S&P 500 Market Analysis

End-to-end data pipeline and dashboard for S&P 500 stocks. Fetches daily prices via yfinance, stores and processes them in BigQuery, and displays key indicators and returns in a Streamlit dashboard.

## Stack

- **Data source:** yfinance (Yahoo Finance) + Wikipedia (S&P 500 ticker list)
- **Backend:** FastAPI + uvicorn
- **Storage:** Google BigQuery
- **Dashboard:** Streamlit + Plotly
- **Deployment:** Cloud Run (FastAPI) via Cloud Build
- **Scheduler:** Cloud Scheduler — runs pipeline Mon–Fri at 23:00 UTC
- **Local dev:** Docker Compose

## How it works

### Pipeline (runs daily automatically)
```
/api/run-pipeline
  → get_tickers        scrape S&P 500 list from Wikipedia → raw.tickers
  → get_daily_prices   fetch OHLCV from yfinance (incremental) → raw.prices
  → compute_returns    calculate daily returns → raw.Prices_with_returns
  → compute_indicators ATR, Keltner Channels, 52W High/Low → raw.Indicators
  → snapshot_today     join all tables → analytics.today_snapshot
  → agg_prices         price arrays (1M, 1Q) → analytics.agg_prices
  → agg_returns        period returns (1W, 1M, 1Q, 1Y) → analytics.agg_returns
```

### Dashboard (3 pages)
- **Screener** — sortable table of all 500 stocks with price, returns, ATR, and sector filter
- **Stock Detail** — candlestick chart + Keltner Channel bands + volume + 52W range position
- **Sector View** — average returns by GICS sector for any period

## BigQuery layout
```
project/
├── raw/
│   ├── tickers              S&P 500 companies (truncate+reload)
│   ├── prices               Daily OHLCV (incremental)
│   ├── Prices_with_returns  prices + daily return
│   ├── IntradayPrices       5m intraday (incremental)
│   └── Indicators           ATR, Keltner Channels, 52W High/Low
└── analytics/
    ├── today_snapshot       Latest price + all indicators per ticker
    ├── agg_prices           Price arrays (last 1M and 1Q)
    └── agg_returns          Cumulative returns by period
```

## Running locally

### Prerequisites
- Docker Desktop
- GCP service account key with BigQuery Data Editor + Job User roles
- `.env` file (copy from `.env.example` and fill in your values)

### Start
```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| FastAPI (pipeline) | http://localhost:8080 |
| FastAPI docs | http://localhost:8080/docs |
| Streamlit dashboard | http://localhost:8501 |

### Trigger pipeline manually
```
http://localhost:8080/api/run-pipeline
```

## Project structure
```
market-analysis/
├── main.py                  FastAPI entry point
├── app/
│   ├── router.py            API routes
│   └── services/            One module per pipeline step
├── dashboard/
│   ├── app.py               Streamlit app (3 pages)
│   └── queries.py           BigQuery queries
├── utils/
│   └── bq.py                Shared BigQuery client
├── Dockerfile               Container definition
├── docker-compose.yml       Local dev (FastAPI + Streamlit)
├── cloudbuild.yaml          CI/CD → Artifact Registry → Cloud Run
└── requirements.txt
```

## Git workflow
- Work on `dev` branch — does **not** trigger Cloud Build
- Merge to `main` to deploy to Cloud Run
