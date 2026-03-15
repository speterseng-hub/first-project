# Market Analysis — Project Context for Claude

## What this is
FastAPI + BigQuery + Streamlit data pipeline and dashboard for S&P 500 stocks.
Fetches daily prices via yfinance, stores in BigQuery, computes indicators and returns, exposes a Streamlit dashboard.

## Stack
- **Backend:** FastAPI + uvicorn
- **Data source:** yfinance (Yahoo Finance), Wikipedia (S&P 500 ticker list)
- **Storage:** Google BigQuery (GCP project: `double-archive-274200`)
- **Dashboard:** Streamlit (in progress)
- **Deployment:** Cloud Run via Cloud Build (triggers on push to `main` only)
- **Local dev:** Docker Compose

## Folder structure
```
market-analysis/
├── main.py                  # FastAPI entry point
├── app/
│   ├── router.py            # All API routes
│   └── services/            # One module per endpoint
│       ├── get_tickers.py       # Scrape S&P 500 → BQ raw.tickers
│       ├── get_daily_prices.py  # yfinance → BQ raw.prices (incremental)
│       ├── get_intraday_prices.py
│       ├── compute_returns.py
│       ├── compute_indicators.py
│       ├── snapshot_today.py
│       ├── agg_prices.py
│       └── agg_returns.py
├── utils/
│   └── bq.py                # Shared BQ client (lazy-init), run_query, insert_rows
├── dashboard/               # Streamlit app (in progress)
│   ├── app.py
│   └── queries.py
├── docker-compose.yml       # Local dev: FastAPI on 8080, Streamlit on 8501
├── Dockerfile               # FastAPI container
├── cloudbuild.yaml          # Cloud Build → Artifact Registry → Cloud Run
└── requirements.txt
```

## BigQuery layout
```
double-archive-274200/
├── raw/
│   ├── tickers              # S&P 500 companies (truncate+reload)
│   ├── prices               # Daily OHLCV (incremental)
│   ├── Prices_with_returns  # prices + daily return column
│   ├── IntradayPrices       # 5m intraday (incremental)
│   └── Indicators           # ATR, Keltner Channels, 52W High/Low
└── analytics/
    ├── today_snapshot       # Latest price + all indicators per ticker
    ├── agg_prices           # Price arrays (1M, 1Q)
    └── agg_returns          # Period returns (1W, 1M, 1Q, 1Y)
```

## Pipeline execution order
```
/api/tickers → /api/daily-prices → /api/returns → /api/indicators
             → /api/snapshot-today → /api/agg-prices → /api/agg-returns
```
All steps run together via `/api/run-pipeline` (called daily by Cloud Scheduler, Mon–Fri 23:00 UTC).

## Environment variables
Defined in `.env` (gitignored). See `.env.example` for the full list.
Key vars: `PROJECT_ID`, `RAW_DS`, `ANALYTICS_DS`, `PRICES_TABLE`, `TICKERS_TABLE`, etc.
Local credentials: `GOOGLE_APPLICATION_CREDENTIALS=./sa-key.json`

## Running locally
```bash
docker-compose up --build
# FastAPI: http://localhost:8080
# Streamlit: http://localhost:8501
```

## Git workflow
- Work on `dev` branch — pushes do NOT trigger Cloud Build
- Merge to `main` only when ready to deploy — triggers Cloud Build automatically
- Cloud Run service: `stock-service` in `us-central1`

## Important rules
- Do NOT make logic changes to existing services without confirming with the user first
- Do NOT change table names or env var names without updating both `.env` and `cloudbuild.yaml`
- Incremental ingestion: `get_daily_prices` and `get_intraday_prices` use MAX(Date) per ticker — do not change to full reload
- `get_tickers` uses truncate+reload (500 rows, intentional)
- Dashboard queries BigQuery directly — does not call FastAPI endpoints
- Keep GCP costs minimal: avoid full table scans where possible, prefer `analytics.*` tables in the dashboard
