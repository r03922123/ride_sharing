"""Dispatch policies — the Strategy seam over rider<->driver matching.

A policy is called each dispatch tick with the currently-waiting riders and
currently-idle drivers; it returns the assignments to make now. Riders it cannot
serve stay waiting and are offered again next tick (FIFO by request time).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from ridepulse.sim.core.city import CityModel
from ridepulse.sim.core.entities import Assignment, Driver, Rider


class DispatchPolicy(ABC):
    name: str = "abstract"

    @abstractmethod
    def assign(
        self,
        pending: list[Rider],
        idle: list[Driver],
        city: CityModel,
        now: pd.Timestamp,
    ) -> list[Assignment]:
        ...


class NearestDriverPolicy(DispatchPolicy):
    """Each waiting rider (FIFO) takes the closest idle driver within
    ``radius_km``; unreachable riders wait for the next tick."""

    name = "nearest_driver"

    def __init__(self, radius_km: float = 3.0) -> None:
        self.radius_km = radius_km

    def assign(
        self,
        pending: list[Rider],
        idle: list[Driver],
        city: CityModel,
        now: pd.Timestamp,
    ) -> list[Assignment]:
        available = list(idle)
        out: list[Assignment] = []
        for rider in sorted(pending, key=lambda r: r.request_ts):
            best: Driver | None = None
            best_km = self.radius_km
            for driver in available:
                km = city.grid.distance_km(driver.zone, rider.origin_zone)
                if km <= best_km:
                    best, best_km = driver, km
            if best is not None:
                available.remove(best)
                out.append(
                    Assignment(rider.rider_id, best.driver_id, now,
                               {"pickup_km": best_km})
                )
        return out


POLICIES: dict[str, type[DispatchPolicy]] = {
    NearestDriverPolicy.name: NearestDriverPolicy,
}


def make_policy(name: str, **params: float) -> DispatchPolicy:
    try:
        cls = POLICIES[name]
    except KeyError:
        raise KeyError(f"unknown dispatch policy {name!r}; known: "
                       f"{', '.join(sorted(POLICIES))}") from None
    return cls(**params)
