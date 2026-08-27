"""One raw row per cleaning rule → a known cleaned frame."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ridepulse.data.clean import clean_month

MONTH = "2023-01"


def _raw(
    pu_dt: str,
    do_dt: str,
    pu: object,
    do: object,
    dist: float,
    pax: object = 1,
) -> dict[str, object]:
    return {
        "tpep_pickup_datetime": pd.Timestamp(pu_dt),
        "tpep_dropoff_datetime": pd.Timestamp(do_dt),
        "PULocationID": pu,
        "DOLocationID": do,
        "trip_distance": dist,
        "passenger_count": pax,
    }


def _raw_fixture() -> pd.DataFrame:
    rows = [
        # --- kept (5 good) ---
        _raw("2023-01-02 08:00", "2023-01-02 08:12", 161, 230, 2.4),
        _raw("2023-01-05 18:30", "2023-01-05 18:55", 132, 48, 9.1),
        _raw("2023-01-10 00:05", "2023-01-10 00:20", 7, 7, 1.2),
        _raw("2023-01-20 12:00", "2023-01-20 12:40", 263, 1, 15.0),
        _raw("2023-01-28 22:00", "2023-01-28 22:03", 100, 101, 0.5),
        # --- kept: null passenger_count is allowed ---
        _raw("2023-01-15 09:00", "2023-01-15 09:10", 50, 51, 1.5, pax=None),
        # --- kept: one survivor of an exact-duplicate pair ---
        _raw("2023-01-18 07:00", "2023-01-18 07:15", 42, 43, 3.0),
        _raw("2023-01-18 07:00", "2023-01-18 07:15", 42, 43, 3.0),
        # --- dropped: pickup before / after the target month ---
        _raw("2022-12-31 23:59", "2023-01-01 00:10", 161, 162, 2.0),
        _raw("2023-02-01 00:01", "2023-02-01 00:20", 161, 162, 2.0),
        # --- dropped: duration <= 0 and > 180 ---
        _raw("2023-01-09 10:00", "2023-01-09 10:00", 161, 162, 2.0),
        _raw("2023-01-09 10:00", "2023-01-09 13:30", 161, 162, 2.0),
        # --- dropped: distance <= 0 and > 100 ---
        _raw("2023-01-11 10:00", "2023-01-11 10:15", 161, 162, 0.0),
        _raw("2023-01-11 11:00", "2023-01-11 11:15", 161, 162, 150.0),
        # --- dropped: zone id out of 1..263 / null ---
        _raw("2023-01-12 10:00", "2023-01-12 10:15", 264, 162, 2.0),
        _raw("2023-01-12 11:00", "2023-01-12 11:15", 161, 265, 2.0),
        _raw("2023-01-12 12:00", "2023-01-12 12:15", None, 162, 2.0),
    ]
    return pd.DataFrame(rows)


def test_clean_month_applies_every_rule(tmp_path: Path) -> None:
    raw_path = tmp_path / "yellow_2023-01.parquet"
    _raw_fixture().to_parquet(raw_path)
    out_path = tmp_path / "cleaned.parquet"

    clean_month(raw_path, MONTH, out_path)
    cleaned = pd.read_parquet(out_path)

    # 5 good + 1 null-pax + 1 dedup survivor = 7
    assert len(cleaned) == 7
    assert set(cleaned.columns) == {
        "pickup_ts",
        "dropoff_ts",
        "pu_location_id",
        "do_location_id",
        "trip_distance",
        "passenger_count",
        "duration_min",
    }
    assert cleaned["pu_location_id"].between(1, 263).all()
    assert cleaned["do_location_id"].between(1, 263).all()
    assert (cleaned["duration_min"] > 0).all()
    assert (cleaned["duration_min"] <= 180).all()
    assert (cleaned["trip_distance"] > 0).all()
    assert (cleaned["trip_distance"] <= 100).all()
    assert cleaned["pickup_ts"].min() >= pd.Timestamp("2023-01-01")
    assert cleaned["pickup_ts"].max() < pd.Timestamp("2023-02-01")
    # dedup: the 07:00 zone-42 trip appears exactly once
    dup = cleaned[
        (cleaned["pu_location_id"] == 42) & (cleaned["do_location_id"] == 43)
    ]
    assert len(dup) == 1
    # null passenger_count preserved
    assert cleaned["passenger_count"].isna().sum() == 1


def test_clean_month_output_is_schema_valid(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.parquet"
    _raw_fixture().to_parquet(raw_path)
    # clean_month runs CleanedTripSchema.validate internally; no raise == pass
    clean_month(raw_path, MONTH, tmp_path / "out.parquet")
