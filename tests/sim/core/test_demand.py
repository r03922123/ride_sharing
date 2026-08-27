from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ridepulse.sim.core.demand import HOURS_PER_WEEK, DemandProfile

BUSY_ZONE = 161


def _cleaned_fixture(weeks: int = 3) -> pd.DataFrame:
    """Zone 161 gets `hour` trips each hour; zone 50 gets a flat 2/hour."""
    rows = []
    start = pd.Timestamp("2023-01-02 00:00")  # Monday
    for h in range(weeks * HOURS_PER_WEEK):
        ts = start + pd.Timedelta(hours=h)
        for z, n in ((BUSY_ZONE, ts.hour), (50, 2)):
            for _ in range(n):
                rows.append(
                    {
                        "pickup_ts": ts + pd.Timedelta(minutes=1),
                        "dropoff_ts": ts + pd.Timedelta(minutes=11),
                        "pu_location_id": z,
                        "do_location_id": z,
                        "trip_distance": 1.0,
                        "passenger_count": 1,
                        "duration_min": 10.0,
                    }
                )
    return pd.DataFrame(rows)


def _profile(tmp_path: Path) -> DemandProfile:
    cleaned = tmp_path / "cleaned.parquet"
    _cleaned_fixture().to_parquet(cleaned)
    return DemandProfile.calibrate(cleaned)


def test_rates_recover_the_pattern(tmp_path: Path) -> None:
    prof = _profile(tmp_path)
    # zone 161 Monday 09:00 -> ~9 pickups/hour -> 9/60 per minute
    monday_9 = pd.Timestamp("2023-01-09 09:00")
    assert prof.arrival_rate(BUSY_ZONE, monday_9) == pytest.approx(9 / 60, rel=1e-6)
    # zone 50 is flat 2/hour everywhere
    assert prof.arrival_rate(50, monday_9) == pytest.approx(2 / 60, rel=1e-6)


def test_rate_non_negative_and_finite_all_week(tmp_path: Path) -> None:
    prof = _profile(tmp_path)
    base = pd.Timestamp("2023-03-06 00:00")  # any Monday
    for h in range(HOURS_PER_WEEK):
        for z in (1, 50, BUSY_ZONE, 263):
            r = prof.arrival_rate(z, base + pd.Timedelta(hours=h))
            assert np.isfinite(r) and r >= 0.0


def test_sampled_daily_total_within_15pct(tmp_path: Path) -> None:
    prof = _profile(tmp_path)
    day0 = pd.Timestamp("2023-02-06 00:00")  # a Monday
    expected = sum(
        prof.arrival_rate(BUSY_ZONE, day0 + pd.Timedelta(hours=h)) * 60
        for h in range(24)
    )
    rng = np.random.default_rng(0)
    totals = [
        len(prof.sample_arrivals(BUSY_ZONE, day0, day0 + pd.Timedelta(days=1), rng))
        for _ in range(40)
    ]
    assert abs(np.mean(totals) - expected) / expected < 0.15


def test_sampling_is_seed_deterministic(tmp_path: Path) -> None:
    prof = _profile(tmp_path)
    t0 = pd.Timestamp("2023-02-06 08:00")
    t1 = t0 + pd.Timedelta(hours=6)
    a = prof.sample_arrivals(BUSY_ZONE, t0, t1, np.random.default_rng(42))
    b = prof.sample_arrivals(BUSY_ZONE, t0, t1, np.random.default_rng(42))
    assert a == b


def test_artifact_round_trip(tmp_path: Path) -> None:
    prof = _profile(tmp_path)
    art = prof.save(tmp_path / "demand_profile.parquet")
    reloaded = DemandProfile.from_artifact(art)
    t = pd.Timestamp("2023-01-09 17:00")
    assert reloaded.arrival_rate(BUSY_ZONE, t) == pytest.approx(
        prof.arrival_rate(BUSY_ZONE, t), rel=1e-6
    )

