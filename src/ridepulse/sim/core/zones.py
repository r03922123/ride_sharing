"""`ZoneMap` — id <-> name <-> borough for the 263 NYC taxi zones.

Defaults to the committed ``sim/core/data/zone_lookup.csv`` (a copy of the TLC
``taxi_zone_lookup.csv``); ``load`` accepts an override path.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_DEFAULT_CSV = Path(__file__).parent / "data" / "zone_lookup.csv"
ZONE_MIN, ZONE_MAX = 1, 263


class ZoneMap:
    def __init__(self, frame: pd.DataFrame) -> None:
        self._name: dict[int, str] = dict(
            zip(frame["zone_id"], frame["zone"], strict=True)
        )
        self._borough: dict[int, str] = dict(
            zip(frame["zone_id"], frame["borough"], strict=True)
        )
        self._by_name: dict[str, int] = {
            n: z for z, n in self._name.items()
        }

    @classmethod
    def load(cls, lookup_csv: str | Path = _DEFAULT_CSV) -> ZoneMap:
        raw = pd.read_csv(lookup_csv)
        raw = raw.rename(
            columns={"LocationID": "zone_id", "Borough": "borough", "Zone": "zone"}
        )
        raw = raw[raw["zone_id"].between(ZONE_MIN, ZONE_MAX)].sort_values("zone_id")
        return cls(raw[["zone_id", "zone", "borough"]].reset_index(drop=True))

    def __len__(self) -> int:
        return len(self._name)

    @property
    def zone_ids(self) -> list[int]:
        return sorted(self._name)

    def _check(self, zone_id: int) -> None:
        if zone_id not in self._name:
            raise KeyError(f"unknown zone id: {zone_id}")

    def name(self, zone_id: int) -> str:
        self._check(zone_id)
        return self._name[zone_id]

    def borough(self, zone_id: int) -> str:
        self._check(zone_id)
        return self._borough[zone_id]

    def id_by_name(self, name: str) -> int:
        try:
            return self._by_name[name]
        except KeyError:
            raise KeyError(f"unknown zone name: {name!r}") from None
