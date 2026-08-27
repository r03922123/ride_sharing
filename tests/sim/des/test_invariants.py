"""Conservation invariants over a full simulation run (spec §11)."""

from __future__ import annotations

import pandas as pd
import pytest

from ridepulse.sim.core.city import CityModel
from ridepulse.sim.des.dispatch import NearestDriverPolicy
from ridepulse.sim.des.simulation import SimConfig, Simulation


@pytest.fixture
def run_df(small_city: CityModel) -> pd.DataFrame:
    cfg = SimConfig(
        city=small_city,
        policy=NearestDriverPolicy(radius_km=10.0),
        start=pd.Timestamp("2023-01-04 07:00"),
        hours=2.0,
        seed=11,
    )
    return Simulation(cfg).run().to_frame()


def test_every_rider_at_most_one_terminal_state(run_df: pd.DataFrame) -> None:
    completed = set(run_df.loc[run_df["kind"] == "TripCompleted", "rider_id"])
    cancelled = set(run_df.loc[run_df["kind"] == "RiderCancelled", "rider_id"])
    assert completed.isdisjoint(cancelled)


def test_no_cancel_after_match(run_df: pd.DataFrame) -> None:
    matched = set(run_df.loc[run_df["kind"] == "RiderMatched", "rider_id"])
    cancelled = set(run_df.loc[run_df["kind"] == "RiderCancelled", "rider_id"])
    assert matched.isdisjoint(cancelled)


def test_lifecycle_ordering_per_rider(run_df: pd.DataFrame) -> None:
    for _rid, g in run_df.groupby("rider_id"):
        seq = g.sort_values(["ts", "seq"])["kind"].tolist()
        # RiderRequested is always first
        assert seq[0] == "RiderRequested"
        if "PickupCompleted" in seq and "TripCompleted" in seq:
            assert seq.index("PickupCompleted") < seq.index("TripCompleted")
        if "RiderMatched" in seq and "PickupCompleted" in seq:
            assert seq.index("RiderMatched") < seq.index("PickupCompleted")


def test_driver_count_constant(run_df: pd.DataFrame, small_city: CityModel) -> None:
    seen = set(run_df["driver_id"].dropna().astype(int))
    fleet = {d.driver_id for d in small_city.drivers}
    assert seen <= fleet


def test_no_driver_double_booked(run_df: pd.DataFrame) -> None:
    """A driver's match -> trip-completed intervals must not overlap."""
    ev = run_df[run_df["kind"].isin(["RiderMatched", "TripCompleted"])]
    for did, g in ev.groupby("driver_id"):
        g = g.sort_values(["ts", "seq"])
        depth = 0
        for kind in g["kind"]:
            depth += 1 if kind == "RiderMatched" else -1
            assert depth in (0, 1), f"driver {did} double-booked"
        assert depth in (0, 1)


def test_at_least_one_completed_trip(run_df: pd.DataFrame) -> None:
    assert (run_df["kind"] == "TripCompleted").sum() > 0
