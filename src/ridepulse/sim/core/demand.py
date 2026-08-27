"""`DemandProfile` — a calibrated (zone x hour-of-week) Poisson arrival model.

Calibration estimates, for each of the 263 zones and 168 hour-of-week slots, the
mean number of pickups per hour (a Poisson rate). ``sample_arrivals`` draws a
piecewise-constant Poisson process from those rates.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ZONE_MIN, ZONE_MAX = 1, 263
HOURS_PER_WEEK = 168


def _hour_of_week(ts: pd.Series) -> pd.Series:
    how = (ts.dt.dayofweek * 24 + ts.dt.hour).to_numpy()
    return pd.Series(how, index=ts.index, dtype="int64")


class DemandProfile:
    """Mean pickups/hour indexed by ``(zone_id, hour_of_week)``."""

    def __init__(self, rates: pd.DataFrame) -> None:
        # rates: columns zone_id, how, rate_per_hour  (dense: 263 x 168)
        self._table = (
            rates.set_index(["zone_id", "how"])["rate_per_hour"].astype(float)
        )
        self._lookup = self._table.to_dict()

    # ---- construction -----------------------------------------------------

    @classmethod
    def calibrate(cls, cleaned_trips_path: str | Path) -> DemandProfile:
        con = duckdb.connect()
        try:
            hourly = con.execute(
                """
                SELECT pu_location_id AS zone_id,
                       date_trunc('hour', pickup_ts) AS ts,
                       COUNT(*) AS pickups
                FROM read_parquet(?)
                GROUP BY 1, 2
                """,
                [str(cleaned_trips_path)],
            ).df()
        finally:
            con.close()

        hours = pd.date_range(hourly["ts"].min(), hourly["ts"].max(), freq="h")
        zones = range(ZONE_MIN, ZONE_MAX + 1)
        grid = pd.MultiIndex.from_product([zones, hours], names=["zone_id", "ts"])
        dense = (
            hourly.set_index(["zone_id", "ts"])
            .reindex(grid, fill_value=0)
            .reset_index()
        )
        dense["how"] = _hour_of_week(dense["ts"])
        rates = (
            dense.groupby(["zone_id", "how"])["pickups"]
            .mean()
            .rename("rate_per_hour")
            .reset_index()
        )
        return cls(cls._densify(rates))

    @staticmethod
    def _densify(rates: pd.DataFrame) -> pd.DataFrame:
        full = pd.MultiIndex.from_product(
            [range(ZONE_MIN, ZONE_MAX + 1), range(HOURS_PER_WEEK)],
            names=["zone_id", "how"],
        )
        return (
            rates.set_index(["zone_id", "how"])
            .reindex(full, fill_value=0.0)
            .reset_index()
        )

    @classmethod
    def from_artifact(cls, path: str | Path) -> DemandProfile:
        return cls(pd.read_parquet(path))

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._table.rename("rate_per_hour").reset_index().to_parquet(
            path, index=False
        )
        return path

    # ---- query ----------------------------------------------------------

    def arrival_rate(self, zone_id: int, when: datetime | pd.Timestamp) -> float:
        """Riders per minute for ``zone_id`` in the hour-of-week of ``when``."""
        ts = pd.Timestamp(when)
        how = int(ts.dayofweek * 24 + ts.hour)
        return float(self._lookup.get((zone_id, how), 0.0)) / 60.0

    def sample_arrivals(
        self,
        zone_id: int,
        t0: datetime | pd.Timestamp,
        t1: datetime | pd.Timestamp,
        rng: np.random.Generator,
    ) -> list[pd.Timestamp]:
        """Draw rider arrival timestamps in ``[t0, t1)`` for ``zone_id``."""
        start, end = pd.Timestamp(t0), pd.Timestamp(t1)
        if end <= start:
            return []
        out: list[pd.Timestamp] = []
        cursor = start
        while cursor < end:
            next_hour = cursor.floor("h") + pd.Timedelta(hours=1)
            slice_end = min(next_hour, end)
            minutes = (slice_end - cursor).total_seconds() / 60.0
            rate = self.arrival_rate(zone_id, cursor)  # per minute
            n = int(rng.poisson(rate * minutes))
            if n:
                offsets = np.sort(rng.uniform(0.0, minutes, size=n))
                out.extend(
                    cursor + pd.Timedelta(minutes=float(m)) for m in offsets
                )
            cursor = slice_end
        return out
