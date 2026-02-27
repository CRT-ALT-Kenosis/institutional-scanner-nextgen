from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import pandas as pd
import yfinance as yf


@dataclass
class OHLCVData:
    daily: pd.DataFrame
    weekly: pd.DataFrame


class DataEngine:
    """
    Shared data loader for the unified app.
    - Uses yfinance to fetch adjusted OHLCV.
    - Provides daily and weekly frames per ticker.
    """

    def __init__(self, auto_adjust: bool = True):
        self.auto_adjust = auto_adjust

    def get_daily_ohlcv(
        self,
        ticker: str,
        period: str = "max",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Wraps yf.download. For long-term weekly logic, period='max' is ideal. [file:49][web:54]
        """
        if start or end:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=self.auto_adjust,
                progress=False,
            )
        else:
            df = yf.download(
                ticker,
                period=period,
                auto_adjust=self.auto_adjust,
                progress=False,
            )

        if df.empty:
            return df

        # Ensure standard column names and order
        cols = ["Open", "High", "Low", "Close", "Volume"]
        return df[cols].copy()

    def to_weekly(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample a daily OHLCV DataFrame to weekly (Friday) bars. [file:49]
        """
        if daily_df.empty:
            return daily_df

        weekly = (
            daily_df.resample("W-FRI")
            .agg(
                {
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum",
                }
            )
            .dropna()
        )
        return weekly

    def get_ohlcv_for_universe(
        self,
        tickers: Iterable[str],
        period: str = "max",
    ) -> Dict[str, OHLCVData]:
        """
        Fetch daily+weekly OHLCV for a set of tickers.
        For now we keep it simple and loop; later we can batch with yf.download(group_by='ticker').
        [web:52][web:82]
        """
        out: Dict[str, OHLCVData] = {}
        for t in tickers:
            try:
                daily = self.get_daily_ohlcv(t, period=period)
                if daily.empty:
                    continue
                weekly = self.to_weekly(daily)
                out[t] = OHLCVData(daily=daily, weekly=weekly)
            except Exception:
                # Skip problematic tickers (delisted, bad symbols, etc.)
                continue
        return out
