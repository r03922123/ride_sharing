from __future__ import annotations

import pandas as pd

from ridepulse.sim.core.city import CityModel
from ridepulse.sim.des.dispatch import NearestDriverPolicy
from ridepulse.sim.des.simulation import SimConfig, Simulation

START = pd.Timestamp("2023-01-04 07:00")


def _config(city: CityModel, seed: int) -> SimConfig:
    return SimConfig(
        city=city,
        policy=NearestDriverPolicy(radius_km=8.0),
        start=START,
        hours=1.0,
        seed=seed,
    )


def test_run_produces_events(small_city: CityModel) -> None:
    log = Simulation(_config(small_city, seed=0)).run()
    df = log.to_frame()
    assert len(df) > 0
    assert set(df["kind"]).issubset(
        {"RiderRequested", "RiderMatched", "RiderCancelled",
         "PickupCompleted", "TripCompleted"}
    )
    # some rides should complete in an hour with 60 drivers
    assert (df["kind"] == "TripCompleted").sum() > 0


def test_same_seed_is_byte_identical(small_city: CityModel) -> None:
    a = Simulation(_config(small_city, seed=7)).run().to_frame()
    b = Simulation(_config(small_city, seed=7)).run().to_frame()
    pd.testing.assert_frame_equal(a, b)


def test_different_seed_differs(small_city: CityModel) -> None:
    a = Simulation(_config(small_city, seed=1)).run().to_frame()
    b = Simulation(_config(small_city, seed=2)).run().to_frame()
    assert not a.equals(b)
