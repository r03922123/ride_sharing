from __future__ import annotations

from pathlib import Path

import pandas as pd

from ridepulse.data.features_eta import build_eta_features


def _cleaned_fixture(n: int = 50) -> pd.DataFrame:
    base = pd.Timestamp("2023-01-02 06:00")
    rows = []
    for i in range(n):
        pu = base + pd.Timedelta(minutes=7 * i)
        do = pu + pd.Timedelta(minutes=10 + (i % 5))
        rows.append(
            {
                "pickup_ts": pu,
                "dropoff_ts": do,
                "pu_location_id": 100 + (i % 3),
                "do_location_id": 200 + (i % 4),
                "trip_distance": 1.0 + i % 7,
                "passenger_count": 1 + i % 3,
                "duration_min": (do - pu).total_seconds() / 60.0,
            }
        )
    return pd.DataFrame(rows)


def _build(tmp_path: Path, n: int = 50) -> pd.DataFrame:
    cleaned = tmp_path / "cleaned.parquet"
    _cleaned_fixture(n).to_parquet(cleaned)
    out = tmp_path / "eta.parquet"
    build_eta_features(cleaned, out)
    return pd.read_parquet(out)


def test_feature_columns_present(tmp_path: Path) -> None:
    df = _build(tmp_path)
    assert list(df.columns) == [
        "pickup_ts", "pu_location_id", "do_location_id", "hour", "dow",
        "trip_distance", "passenger_count", "duration_min", "split",
    ]


def test_duration_matches_pickup_dropoff(tmp_path: Path) -> None:
    df = _build(tmp_path).sort_values("pickup_ts").reset_index(drop=True)
    # fixture row i has a 10 + (i % 5) minute trip
    for i in range(len(df)):
        assert df.loc[i, "duration_min"] == 10 + (i % 5)


def test_hour_and_dow(tmp_path: Path) -> None:
    df = _build(tmp_path)
    first = df.sort_values("pickup_ts").iloc[0]
    assert first["hour"] == 6
    assert first["dow"] == 0  # 2023-01-02 is a Monday (Mon=0)


def test_time_split_has_no_overlap(tmp_path: Path) -> None:
    df = _build(tmp_path)
    train = df[df["split"] == "train"]
    holdout = df[df["split"] == "holdout"]
    assert len(train) > 0 and len(holdout) > 0
    assert train["pickup_ts"].max() < holdout["pickup_ts"].min()
    assert len(holdout) == round(len(df) * 0.2)
