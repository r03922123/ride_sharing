import numpy as np
import pandas as pd

from ridepulse.sim.des.events import (
    EventLog,
    PickupCompleted,
    RiderCancelled,
    RiderMatched,
    RiderRequested,
    TripCompleted,
)
from ridepulse.sim.des.metrics import summarize
from ridepulse.sim.des.observers import EventLogWriter, MetricsCollector

T0 = pd.Timestamp("2023-01-04 08:00")


def _events() -> list:
    ev: list = []
    for rid, wait, cancelled in [(1, 2.0, False), (2, 5.0, False),
                                 (3, 8.0, True), (4, 1.0, False)]:
        ev.append(RiderRequested(T0, rider_id=rid, zone_id=161))
        if cancelled:
            ev.append(RiderCancelled(T0 + pd.Timedelta(minutes=wait), rider_id=rid,
                                     zone_id=161, wait_min=wait))
            continue
        ev.append(RiderMatched(T0 + pd.Timedelta(minutes=wait), rider_id=rid,
                               driver_id=10 + rid, wait_min=wait))
        ev.append(PickupCompleted(T0 + pd.Timedelta(minutes=wait + 4),
                                  rider_id=rid, driver_id=10 + rid))
        ev.append(TripCompleted(T0 + pd.Timedelta(minutes=wait + 15),
                                rider_id=rid, driver_id=10 + rid, zone_id=230))
    return ev


def test_log_writer_captures_all_events() -> None:
    w = EventLogWriter()
    for e in _events():
        w.on_event(e)
    assert len(w.log) == len(_events())


def test_collector_matches_independent_summary() -> None:
    coll = MetricsCollector(n_drivers=5, horizon_min=60.0)
    ref = EventLog()
    for e in _events():
        coll.on_event(e)
        ref.append(e)

    got = coll.result()
    want = summarize(ref.to_frame(), n_drivers=5, horizon_min=60.0)
    assert got == want

    # sanity on the values
    assert got.requests == 4
    assert got.rides_completed == 3
    assert got.cancellations == 1
    assert got.cancel_rate == 0.25
    assert got.mean_wait_min == np.mean([2.0, 5.0, 1.0])
    assert 0.0 <= got.driver_idle_pct <= 1.0
