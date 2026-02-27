from dataclasses import dataclass
from typing import Dict, List, Literal, Iterable, Optional

import numpy as np
import pandas as pd


ModeType = Literal["retest", "base"]


@dataclass
class LeaderResult:
    ticker: str
    mode: ModeType  # "retest" or "base"

    raw_score: float
    norm_score: float
    grade: str  # "full_hit" | "strong" | "watchlist"

    components: Dict[str, float]
    tags: List[str]
    metrics: Dict[str, float]

    is_full_hit: bool
    is_strong: bool
    is_watchlist: bool

    structure: Optional[str] = None  # e.g. "MA_stack", "EMA_bounce", "first_pullback", "base_growth", "base_commodity"


@dataclass
class LeaderConfig:
    # Sector-aware prior run thresholds (copied from SECTOR_RUN_THRESHOLDS). [file:49]
    min_prior_run_pct_by_sector: Dict[str, float]

    # Retest mode thresholds
    min_correction_pct: float = 35.0
    max_correction_pct: float = 90.0

    # Proximity to 200W
    max_dist_to_200w_pct: float = 15.0  # full points inside; partial within 10% outside [file:49]

    # Volume surge scaling: 0 pts at 1x avg, 20 pts at 3x+ [file:49]
    vol_surge_1x_pts: float = 0.0
    vol_surge_3x_pts: float = 20.0

    # Daily ATR band (3–8% default). [file:50]
    min_atr_daily_pct: float = 3.0
    max_atr_daily_pct: float = 8.0

    # Normalisation & grades. [file:49]
    normalization_divisor: float = 1.25
    full_hit_min: float = 80.0
    strong_min: float = 60.0

    # Future: add knobs for base breakout weights, ATR-dot scoring, etc.


def _grade_from_norm(norm_score: float, cfg: LeaderConfig) -> str:
    if norm_score >= cfg.full_hit_min:
        return "full_hit"
    if norm_score >= cfg.strong_min:
        return "strong"
    return "watchlist"


def _build_leader_result(
    ticker: str,
    mode: ModeType,
    raw_score: float,
    components: Dict[str, float],
    tags: List[str],
    metrics: Dict[str, float],
    structure: Optional[str],
    cfg: LeaderConfig,
) -> LeaderResult:
    # Normalise raw score to /100 as in v28/29: norm = min(100, round(raw / 1.25)). [file:49]
    norm = float(min(100.0, round(raw_score / cfg.normalization_divisor)))
    grade = _grade_from_norm(norm, cfg)

    return LeaderResult(
        ticker=ticker,
        mode=mode,
        raw_score=raw_score,
        norm_score=norm,
        grade=grade,
        components=components,
        tags=tags,
        metrics=metrics,
        is_full_hit=(grade == "full_hit"),
        is_strong=(grade == "strong"),
        is_watchlist=(grade == "watchlist"),
        structure=structure,
    )


# ---------- Retest Mode (Mode 1) ----------


def scan_retest_mode(
    ticker: str,
    weekly_df: pd.DataFrame,
    daily_df: pd.DataFrame,
    sector_name: str,
    cfg: LeaderConfig,
) -> LeaderResult:
    """
    Port of score_setup() + supporting weekly/daily checks from scanner_v30. [file:49]

    Uses:
      - Prior run           0–25 pts (sector-aware thresholds)
      - Correction          0–20 pts
      - Volume surge        0–20 pts
      - 200W SMA proximity  0–15 pts
      - 200W SMA slope      0–8  pts (rising/flattening/declining)
      - Daily ATR           5 pts
      - 50D SMA alignment   5 pts
      - EMA10 > EMA20       3 pts
      - Weekly candle pos   2 pts
      - Bonus: U&R, multi-year vol, resistance→support, recovery struct, sector momentum, ADR logic. [file:49]

    For now this is a stub; we will mirror the actual math from scanner_v30 into here.
    """
    components: Dict[str, float] = {}
    tags: List[str] = []
    metrics: Dict[str, float] = {}
    structure: Optional[str] = None

    # TODO: implement full scoring by translating scanner_v30.py.
    raw_score = 0.0

    return _build_leader_result(
        ticker=ticker,
        mode="retest",
        raw_score=raw_score,
        components=components,
        tags=tags,
        metrics=metrics,
        structure=structure,
        cfg=cfg,
    )


# ---------- Base Breakout Mode (Mode 2) ----------


def scan_base_breakout_mode(
    ticker: str,
    weekly_df: pd.DataFrame,
    daily_df: pd.DataFrame,
    sector_name: str,
    cfg: LeaderConfig,
) -> LeaderResult:
    """
    Port of check_base_breakout() + score_base_breakout() from scanner_v30. [file:49]

    Growth weights (from handoff):
      - Vol surge       25 pts
      - Base range %    20 pts
      - SMA proximity   15 pts
      - Base ATR        15 pts
      - Duration        10 pts
      - SMA slope        5 pts
      - Daily ATR        5 pts
      - 50D SMA          5 pts
      - ATR-dot response 0–12 pts
      - EMA cross        3 pts
      - Candle pos       2 pts

    Commodity weights:
      - 200W SMA prox   25 pts
      - Base range %    20 pts
      - Base ATR        20 pts
      - Vol surge       20 pts
      - Duration        10 pts
      - SMA slope        5 pts

    For now this is a stub; we will implement the full scoring later.
    """
    components: Dict[str, float] = {}
    tags: List[str] = []
    metrics: Dict[str, float] = {}
    structure: Optional[str] = None

    raw_score = 0.0

    return _build_leader_result(
        ticker=ticker,
        mode="base",
        raw_score=raw_score,
        components=components,
        tags=tags,
        metrics=metrics,
        structure=structure,
        cfg=cfg,
    )


# ---------- Batch helpers for universes ----------


def scan_universe_retest(
    tickers: Iterable[str],
    weekly_map: Dict[str, pd.DataFrame],
    daily_map: Dict[str, pd.DataFrame],
    sector_map: Dict[str, str],
    cfg: LeaderConfig,
) -> List[LeaderResult]:
    results: List[LeaderResult] = []
    for t in tickers:
        w = weekly_map.get(t)
        d = daily_map.get(t)
        if w is None or d is None or w.empty or d.empty:
            continue
        sector = sector_map.get(t, "Unknown")
        res = scan_retest_mode(t, w, d, sector, cfg)
        results.append(res)
    return results


def scan_universe_base(
    tickers: Iterable[str],
    weekly_map: Dict[str, pd.DataFrame],
    daily_map: Dict[str, pd.DataFrame],
    sector_map: Dict[str, str],
    cfg: LeaderConfig,
) -> List[LeaderResult]:
    results: List[LeaderResult] = []
    for t in tickers:
        w = weekly_map.get(t)
        d = daily_map.get(t)
        if w is None or d is None or w.empty or d.empty:
            continue
        sector = sector_map.get(t, "Unknown")
        res = scan_base_breakout_mode(t, w, d, sector, cfg)
        results.append(res)
    return results
