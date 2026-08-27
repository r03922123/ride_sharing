"""`summarize` — run metrics as a pure function of the event log."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SimMetrics:
    requests: int
    rides_completed: int
    cancellations: int
    cancel_rate: float
    mean_wait_min: float
    median_wait_min: float
    p90_wait_min: float
    driver_idle_pct: float

    def to_dict(self) -> dict[str, float]:
        return {
            "requests": self.requests,
            "rides_completed": self.rides_completed,
            "cancellations": self.cancellations,
            "cancel_rate": round(self.cancel_rate, 4),
            "mean_wait_min": round(self.mean_wait_min, 3),
            "median_wait_min": round(self.median_wait_min, 3),
            "p90_wait_min": round(self.p90_wait_min, 3),
            "driver_idle_pct": round(self.driver_idle_pct, 3),
        }


def summarize(
    events: pd.DataFrame, *, n_drivers: int, horizon_min: float
) -> SimMetrics:
    kind = events["kind"]
    requests = int((kind == "RiderRequested").sum())
    completed = int((kind == "TripCompleted").sum())
    cancels = int((kind == "RiderCancelled").sum())

    matched_wait = events.loc[kind == "RiderMatched", "wait_min"].astype(float)
    wait = pd.Series(matched_wait.tolist(), dtype=float)
    mean_w = float(wait.mean()) if len(wait) else 0.0
    med_w = float(wait.median()) if len(wait) else 0.0
    p90_w = float(wait.quantile(0.90)) if len(wait) else 0.0

    # busy driver-minutes: match -> trip-completed span per completed rider
    matched = (
        events.loc[kind == "RiderMatched", ["rider_id", "ts"]]
        .rename(columns={"ts": "match_ts"})
    )
    trips = (
        events.loc[kind == "TripCompleted", ["rider_id", "ts"]]
        .rename(columns={"ts": "done_ts"})
    )
    spans = matched.merge(trips, on="rider_id", how="inner")
    busy = float(
        ((spans["done_ts"] - spans["match_ts"]).dt.total_seconds() / 60.0).sum()
    )
    capacity = n_drivers * horizon_min
    idle_pct = 1.0 - busy / capacity if capacity > 0 else 0.0

    return SimMetrics(
        requests=requests,
        rides_completed=completed,
        cancellations=cancels,
        cancel_rate=cancels / requests if requests else 0.0,
        mean_wait_min=mean_w,
        median_wait_min=med_w,
        p90_wait_min=p90_w,
        driver_idle_pct=max(0.0, min(1.0, idle_pct)),
    )
