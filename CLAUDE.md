# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is
FastAPI + BigQuery + Streamlit data pipeline and dashboard for S&P 500 stocks.
Fetches daily prices via yfinance, stores in BigQuery, computes indicators and returns, exposes a Streamlit dashboard.

## Stack
- **Backend:** FastAPI + uvicorn
- **Data source:** yfinance (Yahoo Finance), Wikipedia (S&P 500 ticker list)
- **Storage:** Google BigQuery (GCP project: `double-archive-274200`)
- **Dashboard:** Streamlit (3 pages: Screener, Stock Detail, Sector View)
- **Deployment:** Cloud Run via Cloud Build (triggers on push to `main` only)
- **Local dev:** Docker Compose

## Commands

```bash
# Start everything locally (FastAPI on :8080, Streamlit on :8501)
docker-compose up --build

# Rebuild a single service without restarting the other
docker-compose up --build api
docker-compose up --build dashboard

# Trigger a pipeline step manually (FastAPI must be running)
curl http://localhost:8080/api/run-pipeline
curl http://localhost:8080/api/daily-prices

# Health check
curl http://localhost:8080/healthz
```

No test suite exists in this project.

## Folder structure
```
market-analysis/
├── main.py                  # FastAPI entry point
├── app/
│   ├── router.py            # All API routes (prefix: /api)
│   └── services/            # One module per endpoint; each exports run()
│       ├── get_tickers.py       # Scrape S&P 500 → BQ raw.tickers
│       ├── get_daily_prices.py  # yfinance → BQ raw.prices (incremental)
│       ├── get_intraday_prices.py
│       ├── compute_returns.py
│       ├── compute_indicators.py
│       ├── snapshot_today.py
│       ├── agg_prices.py
│       └── agg_returns.py
├── utils/
│   └── bq.py                # Shared BQ client (lazy-init singleton), run_query, insert_rows
├── dashboard/               # Streamlit app
│   ├── app.py               # 3 pages; BQ data cached via @st.cache_data(ttl=3600)
│   └── queries.py           # All BQ queries returning pd.DataFrame
├── docker-compose.yml       # Local dev: FastAPI on 8080, Streamlit on 8501
├── Dockerfile               # FastAPI container
├── Dockerfile.dashboard     # Streamlit container
├── cloudbuild.yaml          # Cloud Build → Artifact Registry → Cloud Run (deploys both services)
└── requirements.txt
```

## BigQuery layout

**Important:** BQ table names have mixed casing — always match exactly as shown.

```
double-archive-274200/
├── raw/
│   ├── tickers              # S&P 500 companies (truncate+reload)
│   ├── prices               # Daily OHLCV (incremental, lowercase)
│   ├── Prices_with_returns  # prices + daily return column (mixed case)
│   ├── IntradayPrices       # 5m intraday (incremental, PascalCase)
│   └── indicators           # ATR, Keltner Channels, 52W High/Low (lowercase)
└── analytics/
    ├── today_snapshot       # Latest price + all indicators per ticker
    ├── agg_prices           # Price arrays (1M, 1Q)
    └── agg_returns          # Period returns (1W, 1M, 1Q, 1Y)
```

Env vars map to these names — see `.env.example` for the full list. Table names in `cloudbuild.yaml` must match `.env`.

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

## Deployment
Cloud Build deploys **two** Cloud Run services on every push to `main`:
- `stock-service` (FastAPI) — built from `Dockerfile`
- `dashboard` (Streamlit) — built from `Dockerfile.dashboard`

Both are deployed to `us-central1` using `market-analysis-sa@<PROJECT_ID>.iam.gserviceaccount.com`.

## Git workflow
- Work on `dev` branch — pushes do NOT trigger Cloud Build
- Merge to `main` only when ready to deploy — triggers Cloud Build automatically

## Important rules
- Do NOT make logic changes to existing services without confirming with the user first
- Do NOT change table names or env var names without updating both `.env` and `cloudbuild.yaml`
- Incremental ingestion: `get_daily_prices` and `get_intraday_prices` use MAX(Date) per ticker — do not change to full reload
- `get_tickers` uses truncate+reload (500 rows, intentional)
- Dashboard queries BigQuery directly — does not call FastAPI endpoints
- Keep GCP costs minimal: avoid full table scans where possible, prefer `analytics.*` tables in the dashboard
- Each service module follows the same pattern: a single `run()` function returns `{"status": "ok", ...}` or `{"status": "error", "error": str(e)}`
