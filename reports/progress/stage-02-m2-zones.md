# Stage 2 — M2 zones

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (15 files) · pytest 50 passed

## Done
- Committed asset `src/ridepulse/sim/core/data/zone_lookup.csv` (copy of TLC
  `taxi_zone_lookup.csv`; gitignore exception for `*.csv` added).
- `src/ridepulse/sim/core/zones.py` — `ZoneMap.load(lookup_csv=<default asset>)`,
  `name` / `borough` / `id_by_name` (all raise `KeyError` on unknown),
  `zone_ids`, `__len__`. Filters lookup rows to 1..263 (drops 264/265).
- `tests/sim/core/test_zones.py` — 263 zones; `1 -> "Newark Airport"/"EWR"`
  round-trip; Midtown Center -> Manhattan; unknown id / name raise.

## Decisions / deviations from plan
- Lookup CSV committed as a package asset so `ZoneMap.load()` works without a
  data build; override path still accepted (matches plan signature).

## Blocked / deferred
- none.

## Next
- M3 demand — `DemandProfile` Poisson (zone x hour-of-week) calibration + CLI.
