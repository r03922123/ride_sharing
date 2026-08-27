import pandas as pd
import pytest

from ridepulse.sim.core.entities import (
    Assignment,
    Driver,
    DriverState,
    IllegalTransition,
    Rider,
    RiderState,
)

TS = pd.Timestamp("2023-01-04 08:00")


def _rider() -> Rider:
    return Rider(1, origin_zone=161, dest_zone=230, request_ts=TS, patience_min=8.0)


def test_rider_happy_path() -> None:
    r = _rider()
    r.set_state(RiderState.MATCHED)
    r.set_state(RiderState.PICKED_UP)
    r.set_state(RiderState.DROPPED_OFF)
    assert r.is_terminal


def test_rider_cancel_from_waiting_or_matched() -> None:
    r = _rider()
    r.set_state(RiderState.CANCELLED)
    assert r.is_terminal
    r2 = _rider()
    r2.set_state(RiderState.MATCHED)
    r2.set_state(RiderState.CANCELLED)


def test_rider_illegal_transitions_raise() -> None:
    r = _rider()
    with pytest.raises(IllegalTransition):
        r.set_state(RiderState.PICKED_UP)  # skips MATCHED
    r.set_state(RiderState.MATCHED)
    r.set_state(RiderState.PICKED_UP)
    with pytest.raises(IllegalTransition):
        r.set_state(RiderState.CANCELLED)  # can't cancel after pickup
    r.set_state(RiderState.DROPPED_OFF)
    with pytest.raises(IllegalTransition):
        r.set_state(RiderState.WAITING)  # terminal


def test_driver_cycle() -> None:
    d = Driver(1, zone=161)
    d.set_state(DriverState.TO_PICKUP)
    d.set_state(DriverState.ON_TRIP)
    d.set_state(DriverState.IDLE)
    d.set_state(DriverState.REPOSITIONING)
    d.set_state(DriverState.IDLE)


def test_driver_illegal_transition_raises() -> None:
    d = Driver(1, zone=161)
    with pytest.raises(IllegalTransition):
        d.set_state(DriverState.ON_TRIP)  # must go via TO_PICKUP


def test_assignment_is_frozen_and_value_equal() -> None:
    a = Assignment(1, 2, TS)
    b = Assignment(1, 2, TS)
    assert a == b
    with pytest.raises(AttributeError):
        a.rider_id = 5  # type: ignore[misc]
