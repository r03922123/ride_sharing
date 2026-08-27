"""SimPy discrete-event simulation of a one-city ride-sharing market.

Time unit is minutes since ``config.start``. A single seeded RNG drives every
random draw, so a run is byte-for-byte reproducible for a given config + seed.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import simpy

from ridepulse.sim.core.city import CityModel
from ridepulse.sim.core.entities import Driver, DriverState, Rider, RiderState
from ridepulse.sim.des.dispatch import DispatchPolicy
from ridepulse.sim.des.events import (
    Event,
    EventLog,
    PickupCompleted,
    RiderCancelled,
    RiderMatched,
    RiderRequested,
    TripCompleted,
)
from ridepulse.sim.des.observers import EventLogWriter, EventObserver


@dataclass
class SimConfig:
    city: CityModel
    policy: DispatchPolicy
    start: pd.Timestamp
    hours: float = 24.0
    patience_min: float = 8.0
    speed_kmh: float = 24.0
    dispatch_interval_min: float = 1.0
    seed: int = 0
    observers: list[EventObserver] = field(default_factory=list)


class Simulation:
    def __init__(self, config: SimConfig) -> None:
        self.cfg = config
        self.env = simpy.Environment()
        self.rng = np.random.default_rng(config.seed)
        self._horizon = config.hours * 60.0
        self._drivers: dict[int, Driver] = {
            d.driver_id: Driver(d.driver_id, d.zone) for d in config.city.drivers
        }
        self._waiting: dict[int, Rider] = {}
        self._request_at: dict[int, float] = {}
        self._next_rider_id = 0
        self._log = EventLog()
        self._writer = EventLogWriter(self._log)
        self._zone_ids = np.array(config.city.grid.zone_ids)
        w = np.array(
            [config.city.demand.total_weekly_pickups(int(z)) for z in self._zone_ids]
        )
        self._dest_weights = w / w.sum() if w.sum() else None

    # ---- helpers -------------------------------------------------------

    def _now_ts(self) -> pd.Timestamp:
        return self.cfg.start + pd.Timedelta(minutes=float(self.env.now))

    def _emit(self, event: Event) -> None:
        self._writer.on_event(event)
        for obs in self.cfg.observers:
            obs.on_event(event)

    def _sample_dest(self, origin: int) -> int:
        w = self._dest_weights
        dest = int(self.rng.choice(self._zone_ids, p=w))
        return dest if dest != origin else int(self.rng.choice(self._zone_ids, p=w))

    # ---- processes ---------------------------------------------------

    def _arrivals(self, zone_id: int) -> Generator[simpy.Event, None, None]:
        demand = self.cfg.city.demand
        while self.env.now < self._horizon:
            rate = demand.arrival_rate(zone_id, self._now_ts())  # per minute
            if rate <= 0.0:
                yield self.env.timeout(60.0)
                continue
            yield self.env.timeout(float(self.rng.exponential(1.0 / rate)))
            if self.env.now >= self._horizon:
                return
            rider = Rider(
                self._next_rider_id, zone_id, self._sample_dest(zone_id),
                self._now_ts(), self.cfg.patience_min,
            )
            self._next_rider_id += 1
            self._waiting[rider.rider_id] = rider
            self._request_at[rider.rider_id] = float(self.env.now)
            self._emit(RiderRequested(self._now_ts(), rider.rider_id, zone_id))
            self.env.process(self._patience(rider))

    def _patience(self, rider: Rider) -> Generator[simpy.Event, None, None]:
        yield self.env.timeout(rider.patience_min)
        if rider.rider_id in self._waiting:
            del self._waiting[rider.rider_id]
            rider.set_state(RiderState.CANCELLED)
            self._emit(
                RiderCancelled(self._now_ts(), rider.rider_id, rider.origin_zone,
                               rider.patience_min)
            )

    def _dispatch_loop(self) -> Generator[simpy.Event, None, None]:
        pol = self.cfg.policy
        while self.env.now < self._horizon:
            yield self.env.timeout(self.cfg.dispatch_interval_min)
            if not self._waiting:
                continue
            idle = [d for d in self._drivers.values()
                    if d.state == DriverState.IDLE]
            if not idle:
                continue
            for a in pol.assign(list(self._waiting.values()), idle,
                                self.cfg.city, self._now_ts()):
                if a.rider_id in self._waiting and self._drivers[a.driver_id].state \
                        == DriverState.IDLE:
                    self.env.process(self._serve(a.rider_id, a.driver_id))

    def _serve(self, rider_id: int, driver_id: int) -> Generator[simpy.Event, None, None]:
        rider = self._waiting.pop(rider_id)
        driver = self._drivers[driver_id]
        wait_min = float(self.env.now) - self._request_at[rider_id]
        rider.set_state(RiderState.MATCHED)
        driver.set_state(DriverState.TO_PICKUP)
        self._emit(RiderMatched(self._now_ts(), rider_id, driver_id, wait_min))

        grid, speed = self.cfg.city.grid, self.cfg.speed_kmh
        yield self.env.timeout(
            grid.travel_time_min(driver.zone, rider.origin_zone, speed)
        )
        driver.zone = rider.origin_zone
        rider.set_state(RiderState.PICKED_UP)
        driver.set_state(DriverState.ON_TRIP)
        self._emit(PickupCompleted(self._now_ts(), rider_id, driver_id))

        yield self.env.timeout(
            grid.travel_time_min(rider.origin_zone, rider.dest_zone, speed)
        )
        driver.zone = rider.dest_zone
        rider.set_state(RiderState.DROPPED_OFF)
        driver.set_state(DriverState.IDLE)
        self._emit(TripCompleted(self._now_ts(), rider_id, driver_id,
                                 rider.dest_zone))

    # ---- entry point ----------------------------------------------

    def run(self) -> EventLog:
        active = [
            int(z) for z in self._zone_ids
            if self.cfg.city.demand.total_weekly_pickups(int(z)) > 0
        ]
        for z in active:
            self.env.process(self._arrivals(z))
        self.env.process(self._dispatch_loop())
        self.env.run(until=self._horizon)
        return self._log
