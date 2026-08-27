"""Clean a raw monthly yellow-taxi parquet into `CleanedTripSchema` rows.

All row filtering happens in DuckDB SQL — a full month is never materialised in
pandas. The cleaned output is pandera-validated before it is trusted downstream;
a violation raises loudly (spec §10).

Cleaning rules (each recorded in `docs/data-dictionary.md`):
  1. pickup timestamp must fall inside the target month
  2. trip duration in (0, 180] minutes
  3. trip_distance in (0, 100] miles
  4. PU/DO location id in 1..263 (drops 264/265 "Unknown" and nulls)
  5. exact-duplicate rows collapsed
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from ridepulse.data.schemas import (
    MAX_DURATION_MIN,
    MAX_TRIP_MILES,
    ZONE_MAX,
    ZONE_MIN,
    CleanedTripSchema,
)

_CLEAN_SQL = f"""
WITH base AS (
    SELECT
        CAST(tpep_pickup_datetime  AS TIMESTAMP) AS pickup_ts,
        CAST(tpep_dropoff_datetime AS TIMESTAMP) AS dropoff_ts,
        CAST(PULocationID AS BIGINT)             AS pu_location_id,
        CAST(DOLocationID AS BIGINT)             AS do_location_id,
        CAST(trip_distance AS DOUBLE)            AS trip_distance,
        CAST(passenger_count AS BIGINT)          AS passenger_count,
        date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 60.0
            AS duration_min
    FROM read_parquet(?)
)
SELECT DISTINCT
    pickup_ts, dropoff_ts, pu_location_id, do_location_id,
    trip_distance, passenger_count, duration_min
FROM base
WHERE pickup_ts >= ? AND pickup_ts < ?
  AND duration_min > 0 AND duration_min <= {MAX_DURATION_MIN}
  AND trip_distance > 0 AND trip_distance <= {MAX_TRIP_MILES}
  AND pu_location_id BETWEEN {ZONE_MIN} AND {ZONE_MAX}
  AND do_location_id BETWEEN {ZONE_MIN} AND {ZONE_MAX}
ORDER BY pickup_ts
"""


def _month_bounds(month: str) -> tuple[str, str]:
    start = date.fromisoformat(f"{month}-01")
    end = (
        date(start.year + 1, 1, 1)
        if start.month == 12
        else date(start.year, start.month + 1, 1)
    )
    return start.isoformat(), end.isoformat()


def clean_month(raw_path: str | Path, month: str, out_path: str | Path) -> Path:
    """Clean ``raw_path`` for ``month`` (``"YYYY-MM"``) and write parquet to
    ``out_path``. Returns ``out_path``. Raises ``pandera`` errors if the cleaned
    frame violates :data:`CleanedTripSchema`.
    """
    raw_path, out_path = Path(raw_path), Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start, end = _month_bounds(month)

    con = duckdb.connect()
    try:
        con.execute(
            "CREATE TEMP TABLE cleaned AS " + _CLEAN_SQL, [str(raw_path), start, end]
        )
        con.execute(
            f"COPY cleaned TO '{out_path.as_posix()}' (FORMAT PARQUET)"  # noqa: S608
        )
        df = con.execute("SELECT * FROM cleaned").df()
    finally:
        con.close()

    CleanedTripSchema.validate(df, lazy=True)
    return out_path
