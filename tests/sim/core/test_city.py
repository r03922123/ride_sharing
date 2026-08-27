from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ridepulse.sim.core.city import CityConfig, CityModel
from ridepulse.sim.core.demand import DemandProfile
from ridepulse.sim.core.grid import CityGrid
from ridepulse.sim.core.zones import ZoneMap


@pytest.fixture
def profile_path(tmp_path: Path) -> Path:
    # zone 161 heavily weighted, zone 50 light, rest zero
    rows = []
    start = pd.Timestamp("2023-01-02 00:00")
    for h in range(3 * 168):
        ts = start + pd.Timedelta(hours=h)
        for z, n in ((161, 20), (50, 1)):
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
    cleaned = tmp_path / "cleaned.parquet"
    pd.DataFrame(rows).to_parquet(cleaned)
    return DemandProfile.calibrate(cleaned).save(tmp_path / "profile.parquet")


def test_build_is_deterministic(profile_path: Path) -> None:
    cfg = CityConfig(n_drivers=200, seed=7, demand_profile_path=profile_path)
    a = CityModel.build(cfg)
    b = CityModel.build(cfg)
    assert [d.zone for d in a.drivers] == [d.zone for d in b.drivers]
    assert len(a.drivers) == 200


def test_exposes_core_components(profile_path: Path) -> None:
    m = CityModel.build(
        CityConfig(n_drivers=10, seed=1, demand_profile_path=profile_path)
    )
    assert isinstance(m.grid, CityGrid)
    assert isinstance(m.zones, ZoneMap)
    assert isinstance(m.demand, DemandProfile)


def test_demand_weighted_placement_favours_busy_zones(profile_path: Path) -> None:
    m = CityModel.build(
        CityConfig(
            n_drivers=1000, seed=3, demand_profile_path=profile_path,
            driver_placement="demand_weighted",
        )
    )
    zones = np.array([d.zone for d in m.drivers])
    # zone 161 carries ~95% of demand -> should get the lion's share of drivers
    assert (zones == 161).mean() > 0.8


def test_uniform_placement_spreads_out(profile_path: Path) -> None:
    m = CityModel.build(
        CityConfig(
            n_drivers=1000, seed=3, demand_profile_path=profile_path,
            driver_placement="uniform",
        )
    )
    zones = {d.zone for d in m.drivers}
    assert len(zones) > 100  # many distinct zones, not concentrated
