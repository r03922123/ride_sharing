"""Hand-computed demand features + the leakage assertion."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ridepulse.data.features_demand import build_demand_features
from ridepulse.data.schemas import ZONE_MAX, ZONE_MIN

# 3 zones carry trips; the grid must still densify to all 263 zones.
TRIP_ZONES = [50, 161, 230]
START = pd.Timestamp("2023-01-02 00:00")  # a Monday
N_HOURS = 26  # enough to exercise lag_1h and lag_24h


def _cleaned_fixture() -> pd.DataFrame:
    """Deterministic trip rows: zone z, hour h gets ((z + h) % 4) trips."""
    rows = []
    for z in TRIP_ZONES:
        for h in range(N_HOURS):
            ts = START + pd.Timedelta(hours=h)
            for _ in range((z + h) % 4):
                rows.append(
                    {
                        "pickup_ts": ts + pd.Timedelta(minutes=5),
                        "dropoff_ts": ts + pd.Timedelta(minutes=15),
                        "pu_location_id": z,
                        "do_location_id": z,
                        "trip_distance": 1.0,
                        "passenger_count": 1,
                        "duration_min": 10.0,
                    }
                )
    return pd.DataFrame(rows)


def _expected_counts(zone: int) -> list[int]:
    return [(zone + h) % 4 for h in range(N_HOURS)]


def _build(tmp_path: Path) -> pd.DataFrame:
    cleaned = tmp_path / "cleaned.parquet"
    _cleaned_fixture().to_parquet(cleaned)
    out = tmp_path / "demand.parquet"
    build_demand_features(cleaned, out)
    return pd.read_parquet(out)


def test_dense_zero_filled_grid(tmp_path: Path) -> None:
    df = _build(tmp_path)
    assert df["zone_id"].nunique() == ZONE_MAX - ZONE_MIN + 1
    assert df["ts"].nunique() == N_HOURS
    assert len(df) == (ZONE_MAX - ZONE_MIN + 1) * N_HOURS
    # a zone with no trips is present and all-zero, not missing
    empty = df[df["zone_id"] == 7]
    assert len(empty) == N_HOURS
    assert (empty["pickups"] == 0).all()


def test_pickup_counts_match_hand_values(tmp_path: Path) -> None:
    df = _build(tmp_path)
    z161 = df[df["zone_id"] == 161].sort_values("ts").reset_index(drop=True)
    assert z161["pickups"].tolist() == _expected_counts(161)


def test_calendar_columns(tmp_path: Path) -> None:
    df = _build(tmp_path)
    row = df[(df["zone_id"] == 161) & (df["ts"] == START)].iloc[0]
    assert row["hour"] == 0
    assert row["dow"] == 0  # 2023-01-02 is a Monday
    # New Year's Day (observed) falls on 2023-01-02
    assert bool(row["is_holiday"]) is True
    later = df[(df["zone_id"] == 161) & (df["ts"] == START + pd.Timedelta(days=1))]
    assert bool(later.iloc[0]["is_holiday"]) is False


def test_lags_match_and_do_not_leak(tmp_path: Path) -> None:
    df = _build(tmp_path)
    z = df[df["zone_id"] == 161].sort_values("ts").reset_index(drop=True)
    counts = _expected_counts(161)

    for i in range(N_HOURS):
        # lag_1h[i] is exactly pickups[i-1], never pickups[i] or later
        if i >= 1:
            assert z.loc[i, "lag_1h"] == counts[i - 1]
            assert z.loc[i, "lag_1h"] != counts[i] or counts[i] == counts[i - 1]
        else:
            assert np.isnan(z.loc[i, "lag_1h"])
        # lag_24h[i] is pickups[i-24]
        if i >= 24:
            assert z.loc[i, "lag_24h"] == counts[i - 24]
        else:
            assert np.isnan(z.loc[i, "lag_24h"])
    # 26-hour fixture never reaches lag_168h
    assert z["lag_168h"].isna().all()


def test_rolling_means_use_only_past(tmp_path: Path) -> None:
    df = _build(tmp_path)
    z = df[df["zone_id"] == 161].sort_values("ts").reset_index(drop=True)
    counts = _expected_counts(161)
    for i in range(N_HOURS):
        window = counts[max(0, i - 24) : i]  # strictly past, up to 24 back
        if window:
            assert z.loc[i, "roll_mean_24h"] == pytest.approx(
                float(np.mean(window)), rel=1e-9
            )
        else:
            assert np.isnan(z.loc[i, "roll_mean_24h"])
