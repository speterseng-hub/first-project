# app/router.py
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

router = APIRouter()

router.get("/get_tickers")(get_tickers.run)
router.get("/get_daily_prices")(get_daily_prices.run)
router.get("/get_intraday_prices")(get_intraday_prices.run)
router.get("/compute_returns")(compute_returns.run)
router.get("/compute_indicators")(compute_indicators.run)
router.get("/snapshot_today")(snapshot_today.run)
router.get("/agg_prices")(agg_prices.run)
router.get("/agg_returns")(agg_returns.run)
