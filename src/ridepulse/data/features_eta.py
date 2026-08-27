"""Build the ETA feature table from cleaned trips.

Target is `duration_min` (already computed and range-checked in cleaning).
Features: PU/DO zone, pickup `hour` / `dow`, `trip_distance`, `passenger_count`.
A time-ordered `split` column marks the last ``HOLDOUT_FRACTION`` of trips (by
pickup time) as ``holdout``; train and holdout never share a timestamp.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from ridepulse.data.schemas import EtaFeatureSchema

HOLDOUT_FRACTION = 0.2


def _load(cleaned_path: Path) -> pd.DataFrame:
    con = duckdb.connect()
    try:
        return con.execute(
            """
            SELECT
                pickup_ts,
                pu_location_id,
                do_location_id,
                CAST(hour(pickup_ts)      AS BIGINT) AS hour,
                CAST(dayofweek(pickup_ts) AS BIGINT) AS dow,
                trip_distance,
                passenger_count,
                CAST(date_diff('second', pickup_ts, dropoff_ts) / 60.0 AS DOUBLE)
                    AS duration_min
            FROM read_parquet(?)
            ORDER BY pickup_ts
            """,
            [str(cleaned_path)],
        ).df()
    finally:
        con.close()


def _time_split(df: pd.DataFrame) -> pd.Series:
    """A ``train`` / ``holdout`` label with no shared timestamp at the boundary."""
    cut_idx = int(len(df) * (1.0 - HOLDOUT_FRACTION))
    cut_idx = min(max(cut_idx, 1), len(df) - 1)
    cutoff_ts = df["pickup_ts"].iloc[cut_idx]
    return pd.Series(
        ["train" if t < cutoff_ts else "holdout" for t in df["pickup_ts"]],
        index=df.index,
        dtype="object",
    )


def build_eta_features(cleaned_path: str | Path, out_path: str | Path) -> Path:
    """Read cleaned trips, emit the `EtaFeatureSchema` table to ``out_path``."""
    cleaned_path, out_path = Path(cleaned_path), Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = _load(cleaned_path)
    # DuckDB dayofweek: Sunday=0..Saturday=6; shift to Monday=0..Sunday=6.
    df["dow"] = (df["dow"] - 1) % 7
    df["split"] = _time_split(df)

    cols = [
        "pickup_ts", "pu_location_id", "do_location_id", "hour", "dow",
        "trip_distance", "passenger_count", "duration_min", "split",
    ]
    df = df[cols]
    EtaFeatureSchema.validate(df, lazy=True)
    df.to_parquet(out_path, index=False)
    return out_path
