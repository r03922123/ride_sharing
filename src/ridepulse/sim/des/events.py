"""Simulation events and the append-only `EventLog`.

The log is the single source of truth for a run; metrics are always a pure
function of it (see `metrics.summarize`).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

_COLUMNS = [
    "seq", "kind", "ts", "rider_id", "driver_id", "zone_id", "to_zone_id",
    "wait_min",
]


@dataclass(frozen=True)
class Event:
    ts: pd.Timestamp

    @property
    def kind(self) -> str:
        return type(self).__name__


@dataclass(frozen=True)
class RiderRequested(Event):
    rider_id: int
    zone_id: int


@dataclass(frozen=True)
class RiderMatched(Event):
    rider_id: int
    driver_id: int
    wait_min: float


@dataclass(frozen=True)
class RiderCancelled(Event):
    rider_id: int
    zone_id: int
    wait_min: float


@dataclass(frozen=True)
class PickupCompleted(Event):
    rider_id: int
    driver_id: int


@dataclass(frozen=True)
class TripCompleted(Event):
    rider_id: int
    driver_id: int
    zone_id: int


@dataclass(frozen=True)
class DriverRepositioned(Event):
    driver_id: int
    zone_id: int
    to_zone_id: int


class EventLog:
    def __init__(self) -> None:
        self._rows: list[dict[str, object]] = []

    def append(self, event: Event) -> None:
        self._rows.append(
            {"seq": len(self._rows), "kind": event.kind, **asdict(event)}
        )

    def __len__(self) -> int:
        return len(self._rows)

    def to_frame(self) -> pd.DataFrame:
        df = pd.DataFrame(self._rows)
        for col in _COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA
        # (ts, seq) is a total causal order: seq is the emission index.
        df = df[_COLUMNS].sort_values(["ts", "seq"]).reset_index(drop=True)
        df["seq"] = df["seq"].astype("int64")
        df["kind"] = df["kind"].astype("string")
        df["ts"] = pd.to_datetime(df["ts"])
        for col in ("rider_id", "driver_id", "zone_id", "to_zone_id"):
            df[col] = df[col].astype("Int64")
        df["wait_min"] = df["wait_min"].astype("Float64")
        return df

    def to_parquet(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_frame().to_parquet(path, index=False)
        return path

    @classmethod
    def from_parquet(cls, path: str | Path) -> pd.DataFrame:
        return pd.read_parquet(path)
