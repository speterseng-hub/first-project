# dashboard/app.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dashboard.queries import (
    get_screener,
    get_price_history,
    get_indicators,
    get_sector_returns,
    get_tickers_list,
)

st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")

@st.cache_data(ttl=3600)
def load_screener():
    return get_screener()

@st.cache_data(ttl=3600)
def load_sector_returns():
    return get_sector_returns()

@st.cache_data(ttl=3600)
def load_tickers():
    return get_tickers_list()

@st.cache_data(ttl=3600)
def load_stock(ticker):
    return get_price_history(ticker), get_indicators(ticker)

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.title("S&P 500 Dashboard")
page = st.sidebar.radio("", ["Screener", "Stock Detail", "Sector View"])

# ── PAGE 1: Screener ──────────────────────────────────────────────────────────
if page == "Screener":
    st.title("S&P 500 Screener")

    df = load_screener()

    # Filters
    col1, col2 = st.columns([2, 1])
    with col1:
        sectors = ["All"] + sorted(df["GICS_Sector"].dropna().unique().tolist())
        sector = st.selectbox("Sector", sectors)
    with col2:
        sort_by = st.selectbox("Sort by", ["OneMonth_pct", "OneWeek_pct", "OneQuarter_pct", "OneYear_pct", "Price", "ATR"])

    if sector != "All":
        df = df[df["GICS_Sector"] == sector]

    df = df.sort_values(sort_by, ascending=False).reset_index(drop=True)

    # Color returns
    def color_return(val):
        if val is None:
            return ""
        color = "green" if val > 0 else "red"
        return f"color: {color}"

    return_cols = ["DayReturn_pct", "OneWeek_pct", "OneMonth_pct", "OneQuarter_pct", "OneYear_pct"]
    styled = df.style.applymap(color_return, subset=return_cols).format({
        "Price": "${:.2f}",
        "DayReturn_pct": "{:.2f}%",
        "OneWeek_pct": "{:.2f}%",
        "OneMonth_pct": "{:.2f}%",
        "OneQuarter_pct": "{:.2f}%",
        "OneYear_pct": "{:.2f}%",
        "ATR": "{:.2f}",
        "Position_52W_pct": "{:.1f}%",
    }, na_rep="-")

    st.dataframe(styled, use_container_width=True, height=600)

# ── PAGE 2: Stock Detail ──────────────────────────────────────────────────────
elif page == "Stock Detail":
    st.title("Stock Detail")

    tickers = load_tickers()
    ticker = st.sidebar.selectbox("Select Ticker", tickers)

    prices, indicators = load_stock(ticker)

    if prices.empty:
        st.warning("No price data available for this ticker.")
        st.stop()

    # Merge prices + indicators
    prices["Date"] = prices["Date"].astype(str)
    indicators["Date"] = indicators["Date"].astype(str)
    df = prices.merge(indicators[["Date", "KCUpper", "KCLower"]], on="Date", how="left")

    # Snapshot metrics
    screener = load_screener()
    snap = screener[screener["Ticker"] == ticker]
    if not snap.empty:
        s = snap.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Price", f"${s['Price']:.2f}", f"{s['DayReturn_pct']:.2f}%")
        c2.metric("1 Week", f"{s['OneWeek_pct']:.2f}%")
        c3.metric("1 Month", f"{s['OneMonth_pct']:.2f}%")
        c4.metric("1 Quarter", f"{s['OneQuarter_pct']:.2f}%")
        c5.metric("1 Year", f"{s['OneYear_pct']:.2f}%")

    # Price chart + volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Price"
    ), row=1, col=1)

    # Keltner Channel
    if df["KCUpper"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["KCUpper"],
            line=dict(color="rgba(100,149,237,0.6)", dash="dot"),
            name="KC Upper"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["KCLower"],
            line=dict(color="rgba(100,149,237,0.6)", dash="dot"),
            fill="tonexty", fillcolor="rgba(100,149,237,0.08)",
            name="KC Lower"
        ), row=1, col=1)

    # Volume
    colors = ["green" if c >= o else "red" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df["Date"], y=df["Volume"],
        marker_color=colors, name="Volume", showlegend=False
    ), row=2, col=1)

    fig.update_layout(
        title=f"{ticker} — Last 6 Months",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 52W range bar
    if not snap.empty:
        pos = s["Position_52W_pct"]
        if pos is not None:
            st.markdown(f"**52-Week Range Position: {pos:.1f}%**")
            st.progress(min(max(int(pos), 0), 100))

# ── PAGE 3: Sector View ───────────────────────────────────────────────────────
elif page == "Sector View":
    st.title("Returns by Sector")

    df = load_sector_returns()

    period = st.radio("Period", ["OneWeek_pct", "OneMonth_pct", "OneQuarter_pct", "OneYear_pct"],
                      format_func=lambda x: x.replace("_pct", "").replace("One", "1 "),
                      horizontal=True)

    df_sorted = df.sort_values(period, ascending=True)

    colors = ["green" if v >= 0 else "red" for v in df_sorted[period]]
    fig = go.Figure(go.Bar(
        x=df_sorted[period],
        y=df_sorted["Sector"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}%" for v in df_sorted[period]],
        textposition="outside"
    ))
    fig.update_layout(
        height=500,
        template="plotly_dark",
        xaxis_title="Return (%)",
        margin=dict(l=200)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df.set_index("Sector").style.format("{:.2f}%").applymap(
            lambda v: "color: green" if v > 0 else "color: red"
        ),
        use_container_width=True
    )
