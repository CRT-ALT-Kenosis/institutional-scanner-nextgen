import streamlit as st

from data_engine import DataEngine
from leader_engine import (
    LeaderConfig,
    scan_universe_retest,
)

# ---- Basic Streamlit page setup ----

st.set_page_config(
    page_title="Unified Institutional Scanner (Alpha)",
    layout="wide",
    page_icon="📊",
)

st.title("Unified Institutional Scanner (Alpha)")

st.write(
    "This prototype runs the Market Leader **Retest Mode** engine over a small universe "
    "using the new shared `leader_engine` and `data_engine` modules."
)

# ---- Sidebar: universe input ----

st.sidebar.header("Universe")
tickers_text = st.sidebar.text_area(
    "Tickers (comma-separated)",
    value="TPL, NVDA, AMD, META, TSLA, PLTR, KGC, BHP, PYPL, ENPH",
)
run_button = st.sidebar.button("Run Retest Mode Scan")


# For now, sector map is dummy; we'll integrate your real sector map later. [file:49]
def build_dummy_sector_map(tickers):
    return {t: "Technology" for t in tickers}


# ---- Configure Leader Engine (using your sector thresholds) ----

default_sector_thresholds = {
    "Energy": 150.0,
    "Basic Materials": 150.0,
    "Utilities": 80.0,
    "Consumer Defensive": 100.0,
    "Real Estate": 120.0,
    "Technology": 300.0,
    "Communication": 300.0,
    "Healthcare": 200.0,
    "Consumer Cyclical": 200.0,
    "Industrials": 150.0,
    "Financials": 150.0,
    "Gold Miners": 200.0,
}  # from SECTOR_RUN_THRESHOLDS [file:49]

leader_cfg = LeaderConfig(min_prior_run_pct_by_sector=default_sector_thresholds)

# ---- Run scan on button click ----

if run_button:
    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    if not tickers:
        st.error("Please enter at least one ticker.")
        st.stop()

    engine = DataEngine(auto_adjust=True)

    with st.spinner("Fetching OHLCV data via yfinance and running Retest Mode scan..."):
        ohlcv_map = engine.get_ohlcv_for_universe(tickers, period="max")
        if not ohlcv_map:
            st.error("No OHLCV data fetched. Check tickers or try again.")
            st.stop()

        weekly_map = {t: data.weekly for t, data in ohlcv_map.items()}
        daily_map = {t: data.daily for t, data in ohlcv_map.items()}
        sector_map = build_dummy_sector_map(weekly_map.keys())

        results = scan_universe_retest(
            tickers=weekly_map.keys(),
            weekly_map=weekly_map,
            daily_map=daily_map,
            sector_map=sector_map,
            cfg=leader_cfg,
        )

    if not results:
        st.info(
            "Scan completed but no results were returned. "
            "This is expected while the scoring functions are still stubbed."
        )
        st.stop()

    # Sort by norm_score descending
    results = sorted(results, key=lambda r: r.norm_score, reverse=True)

    st.subheader("Retest Mode Results")

    for res in results:
        # Minimal card-style layout; later we can port your full card design. [file:49]
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"**{res.ticker}**")
                st.write("Mode: Retest")
                st.write(f"Grade: {res.grade} (score {res.norm_score:.1f})")
                if res.tags:
                    st.write("Tags: " + " · ".join(res.tags))

            with col2:
                st.write("Components:")
                if res.components:
                    for name, val in res.components.items():
                        st.write(f"- {name}: {val:.1f}")
                else:
                    st.write("- (components not yet implemented)")

            with col3:
                st.write("Key metrics:")
                if res.metrics:
                    for name, val in list(res.metrics.items())[:5]:
                        try:
                            st.write(f"- {name}: {float(val):.2f}")
                        except Exception:
                            st.write(f"- {name}: {val}")
                else:
                    st.write("- (metrics not yet implemented)")
