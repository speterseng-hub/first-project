from fastapi import APIRouter
from app.services import (
    get_tickers,
    get_daily_prices,
    get_intraday_prices,
    compute_returns,
    compute_indicators,
    snapshot_today,
    agg_prices,
    agg_returns
)

router = APIRouter(prefix="/api", tags=["Stock Analytics"])

@router.get("/tickers", summary="Get available tickers")
def get_tickers_endpoint():
    return get_tickers.run()

@router.get("/daily-prices", summary="Get daily prices")
def get_daily_prices_endpoint():
    return get_daily_prices.run()

@router.get("/intraday-prices", summary="Get intraday prices")
def get_intraday_prices_endpoint(
    interval: str = "5m",
    period: str = "1d"
    ):
    return get_intraday_prices.run(
        interval=interval,
        period=period
    )

@router.get("/returns", summary="Compute returns")
def compute_returns_endpoint():
    return compute_returns.run()

@router.get("/indicators", summary="Compute indicators")
def compute_indicators_endpoint():
    return compute_indicators.run()

@router.get("/snapshot-today", summary="Snapshot today's prices")
def snapshot_today_endpoint():
    return snapshot_today.run()

@router.get("/agg-prices", summary="Aggregate prices")
def agg_prices_endpoint():
    return agg_prices.run()

@router.get("/agg-returns", summary="Aggregate returns")
def agg_returns_endpoint():
    return agg_returns.run()
