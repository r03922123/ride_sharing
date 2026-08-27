"""Build the demand feature table: pickups per zone per hour, on a dense
zero-filled (zone x hour) grid, with calendar, lag, and rolling-mean features.

Leakage discipline: every lag/rolling column at timestamp ``t`` is computed from
values **strictly before ``t``** (``shift(1)`` before any window). The row for
``t`` never sees its own ``pickups`` or anything later. This is asserted in
``tests/data/test_features_demand.py``.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import holidays
import pandas as pd

from ridepulse.data.schemas import ZONE_MAX, ZONE_MIN, DemandFeatureSchema

_LAGS = {"lag_1h": 1, "lag_24h": 24, "lag_168h": 168}
_ROLLS = {"roll_mean_24h": 24, "roll_mean_168h": 168}


def _hourly_counts(cleaned_path: Path) -> pd.DataFrame:
    con = duckdb.connect()
    try:
        return con.execute(
            """
            SELECT
                date_trunc('hour', pickup_ts) AS ts,
                pu_location_id                 AS zone_id,
                COUNT(*)                       AS pickups
            FROM read_parquet(?)
            GROUP BY 1, 2
            """,
            [str(cleaned_path)],
        ).df()
    finally:
        con.close()


def _dense_grid(counts: pd.DataFrame) -> pd.DataFrame:
    hours = pd.date_range(counts["ts"].min(), counts["ts"].max(), freq="h")
    zones = range(ZONE_MIN, ZONE_MAX + 1)
    index = pd.MultiIndex.from_product([zones, hours], names=["zone_id", "ts"])
    dense = (
        counts.set_index(["zone_id", "ts"])
        .reindex(index, fill_value=0)
        .reset_index()
        .sort_values(["zone_id", "ts"])
        .reset_index(drop=True)
    )
    dense["pickups"] = dense["pickups"].astype("int64")
    return dense


def _add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    ts = df["ts"].dt
    df["hour"] = ts.hour.astype("int64")
    df["dow"] = ts.dayofweek.astype("int64")
    years = range(df["ts"].min().year, df["ts"].max().year + 1)
    us = holidays.country_holidays("US", years=list(years))
    df["is_holiday"] = df["ts"].dt.date.map(lambda d: d in us).astype(bool)
    return df


def _add_lags_and_rolls(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("zone_id", sort=False)["pickups"]
    past = grp.shift(1)  # strictly-past series, aligned per zone
    for name, k in _LAGS.items():
        df[name] = grp.shift(k).astype("float64")
    past_by_zone = df.assign(_past=past).groupby("zone_id", sort=False)["_past"]
    for name, w in _ROLLS.items():
        df[name] = (
            past_by_zone.rolling(window=w, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
            .astype("float64")
        )
    return df


def build_demand_features(
    cleaned_path: str | Path, out_path: str | Path
) -> Path:
    """Read cleaned trips, emit the `DemandFeatureSchema` table to ``out_path``."""
    cleaned_path, out_path = Path(cleaned_path), Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = _dense_grid(_hourly_counts(cleaned_path))
    df = _add_calendar(df)
    df = _add_lags_and_rolls(df)

    cols = [
        "zone_id", "ts", "pickups", "hour", "dow", "is_holiday",
        *_LAGS, *_ROLLS,
    ]
    df = df[cols]
    DemandFeatureSchema.validate(df, lazy=True)
    df.to_parquet(out_path, index=False)
    return out_path
