from pathlib import Path

import pandas as pd

from ridepulse.sim.des.events import (
    EventLog,
    PickupCompleted,
    RiderCancelled,
    RiderMatched,
    RiderRequested,
    TripCompleted,
)

T0 = pd.Timestamp("2023-01-04 08:00")


def _log() -> EventLog:
    log = EventLog()
    log.append(RiderRequested(T0, rider_id=1, zone_id=161))
    log.append(RiderMatched(T0 + pd.Timedelta(minutes=2), rider_id=1, driver_id=7,
                            wait_min=2.0))
    log.append(PickupCompleted(T0 + pd.Timedelta(minutes=6), rider_id=1, driver_id=7))
    log.append(TripCompleted(T0 + pd.Timedelta(minutes=20), rider_id=1, driver_id=7,
                             zone_id=230))
    log.append(RiderRequested(T0 + pd.Timedelta(minutes=1), rider_id=2, zone_id=50))
    log.append(RiderCancelled(T0 + pd.Timedelta(minutes=9), rider_id=2, zone_id=50,
                              wait_min=8.0))
    return log


def test_event_kind_is_class_name() -> None:
    assert RiderRequested(T0, 1, 161).kind == "RiderRequested"


def test_to_frame_is_sorted_and_has_all_columns() -> None:
    df = _log().to_frame()
    assert len(df) == 6
    assert df["ts"].is_monotonic_increasing
    assert {"kind", "ts", "rider_id", "driver_id", "zone_id", "to_zone_id",
            "wait_min"} == set(df.columns)
    assert df.iloc[0]["kind"] == "RiderRequested"


def test_parquet_round_trip(tmp_path: Path) -> None:
    log = _log()
    path = log.to_parquet(tmp_path / "events.parquet")
    back = EventLog.from_parquet(path)
    pd.testing.assert_frame_equal(back, log.to_frame())
