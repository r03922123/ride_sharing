"""`CityModel` — the shared, deterministic starting state both simulators build on.

Bundles the grid, zone map, and calibrated demand profile, plus an initial
driver fleet placed either uniformly at random or weighted by total zone demand.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from ridepulse.sim.core.demand import ZONE_MAX, ZONE_MIN, DemandProfile
from ridepulse.sim.core.entities import Driver
from ridepulse.sim.core.grid import CityGrid
from ridepulse.sim.core.zones import ZoneMap

Placement = Literal["uniform", "demand_weighted"]


@dataclass(frozen=True)
class CityConfig:
    n_drivers: int
    seed: int
    demand_profile_path: str | Path
    driver_placement: Placement = "demand_weighted"


class CityModel:
    def __init__(
        self,
        grid: CityGrid,
        zones: ZoneMap,
        demand: DemandProfile,
        drivers: list[Driver],
    ) -> None:
        self.grid = grid
        self.zones = zones
        self.demand = demand
        self.drivers = drivers

    @classmethod
    def build(cls, config: CityConfig) -> CityModel:
        grid = CityGrid.load()
        zones = ZoneMap.load()
        demand = DemandProfile.from_artifact(config.demand_profile_path)
        rng = np.random.default_rng(config.seed)

        zone_ids = np.arange(ZONE_MIN, ZONE_MAX + 1)
        if config.driver_placement == "demand_weighted":
            w = np.array([demand.total_weekly_pickups(int(z)) for z in zone_ids])
            weights = w / w.sum() if w.sum() else None
        else:
            weights = None

        home = rng.choice(zone_ids, size=config.n_drivers, p=weights)
        drivers = [Driver(driver_id=i, zone=int(z)) for i, z in enumerate(home)]
        return cls(grid, zones, demand, drivers)
