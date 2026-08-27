from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ridepulse.sim.core.city import CityConfig, CityModel
from ridepulse.sim.core.demand import DemandProfile


@pytest.fixture
def small_city(tmp_path: Path) -> CityModel:
    """A CityModel with demand concentrated in a few Manhattan-ish zones."""
    rows = []
    start = pd.Timestamp("2023-01-02 00:00")
    for h in range(2 * 168):
        ts = start + pd.Timedelta(hours=h)
        for z, n in ((161, 12), (162, 8), (230, 6), (48, 4)):
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
    profile = DemandProfile.calibrate(cleaned).save(tmp_path / "profile.parquet")
    return CityModel.build(
        CityConfig(n_drivers=60, seed=1, demand_profile_path=profile)
    )
