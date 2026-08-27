"""Rider and Driver entities with explicit, enforced state machines.

Illegal transitions raise :class:`IllegalTransition` — the simulator relies on
this to catch lifecycle bugs (see the Stage 3 conservation invariants).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import pandas as pd


class IllegalTransition(RuntimeError):
    pass


class RiderState(StrEnum):
    WAITING = "waiting"
    MATCHED = "matched"
    PICKED_UP = "picked_up"
    DROPPED_OFF = "dropped_off"
    CANCELLED = "cancelled"


class DriverState(StrEnum):
    IDLE = "idle"
    TO_PICKUP = "to_pickup"
    ON_TRIP = "on_trip"
    REPOSITIONING = "repositioning"


_RIDER_LEGAL: dict[RiderState, set[RiderState]] = {
    RiderState.WAITING: {RiderState.MATCHED, RiderState.CANCELLED},
    RiderState.MATCHED: {RiderState.PICKED_UP, RiderState.CANCELLED},
    RiderState.PICKED_UP: {RiderState.DROPPED_OFF},
    RiderState.DROPPED_OFF: set(),
    RiderState.CANCELLED: set(),
}

_DRIVER_LEGAL: dict[DriverState, set[DriverState]] = {
    DriverState.IDLE: {DriverState.TO_PICKUP, DriverState.REPOSITIONING},
    DriverState.TO_PICKUP: {DriverState.ON_TRIP, DriverState.IDLE},
    DriverState.ON_TRIP: {DriverState.IDLE},
    DriverState.REPOSITIONING: {DriverState.IDLE, DriverState.TO_PICKUP},
}


@dataclass
class Rider:
    rider_id: int
    origin_zone: int
    dest_zone: int
    request_ts: pd.Timestamp
    patience_min: float
    state: RiderState = RiderState.WAITING

    def set_state(self, new: RiderState) -> None:
        if new not in _RIDER_LEGAL[self.state]:
            raise IllegalTransition(f"rider {self.state.value} -> {new.value}")
        self.state = new

    @property
    def is_terminal(self) -> bool:
        return self.state in (RiderState.DROPPED_OFF, RiderState.CANCELLED)


@dataclass
class Driver:
    driver_id: int
    zone: int
    state: DriverState = DriverState.IDLE

    def set_state(self, new: DriverState) -> None:
        if new not in _DRIVER_LEGAL[self.state]:
            raise IllegalTransition(f"driver {self.state.value} -> {new.value}")
        self.state = new


@dataclass(frozen=True)
class Assignment:
    rider_id: int
    driver_id: int
    ts: pd.Timestamp
    _meta: dict[str, float] = field(default_factory=dict, compare=False)
