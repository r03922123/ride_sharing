"""`CityGrid` — zone-centroid distances and a simple travel-time model.

Backed by the committed assets in ``sim/core/data/`` (built once by
``scripts/build_zone_geometry.py``). Travel time is straight-line distance at a
constant speed — deliberately crude; a routing model is out of scope.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd

_DATA = Path(__file__).parent / "data"


class CityGrid:
    def __init__(
        self, zone_ids: list[int], distances_km: npt.NDArray[np.float64]
    ) -> None:
        if distances_km.shape != (len(zone_ids), len(zone_ids)):
            raise ValueError("distance matrix shape does not match zone_ids")
        self._ids = list(zone_ids)
        self._idx = {z: i for i, z in enumerate(self._ids)}
        self._d = distances_km

    @classmethod
    def load(cls) -> CityGrid:
        centroids = pd.read_parquet(_DATA / "zone_centroids.parquet")
        distances = np.load(_DATA / "zone_distances.npy")
        return cls(centroids["zone_id"].astype(int).tolist(), distances)

    @property
    def zone_ids(self) -> list[int]:
        return list(self._ids)

    def distance_km(self, a: int, b: int) -> float:
        try:
            return float(self._d[self._idx[a], self._idx[b]])
        except KeyError as exc:
            raise KeyError(f"unknown zone id: {exc.args[0]}") from None

    def travel_time_min(self, a: int, b: int, speed_kmh: float) -> float:
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be positive")
        return self.distance_km(a, b) / speed_kmh * 60.0
