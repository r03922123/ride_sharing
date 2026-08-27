# Stage 2 — M3 demand

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (16 files) · pytest 55 passed

## Done
- `src/ridepulse/sim/core/demand.py` — `DemandProfile`:
  - `calibrate(cleaned_trips_path)` — DuckDB hourly pickup counts → dense
    (zone 1..263 × every hour) grid → mean pickups/hour per (zone_id,
    hour-of-week) → dense 263×168 rate table. (D8.)
  - `save` / `from_artifact` (parquet).
  - `arrival_rate(zone, when)` → riders **per minute** for that hour-of-week slot.
  - `sample_arrivals(zone, t0, t1, rng)` — piecewise-constant Poisson process,
    hour-by-hour, uniform placement within each slice; seed-deterministic.
- CLI `ridepulse sim calibrate --root data --out configs/sim/demand_profile.parquet`.
- `tests/sim/core/test_demand.py` — 5 tests: rates recover the fixture pattern
  (zone-161 hour-h → h/60 per min; zone-50 flat 2/60); non-negative/finite for
  every zone across a full week; sampled daily total within **±15 %** of the
  expected rate-sum (40 seeds); seed-deterministic; artifact round-trip.

## Real-data smoke
- `calibrate` on `cleaned_trips` (2 months): **0.1 s**. zone 161 Fri 18:00 =
  436.8 pickups/h (plausible Midtown rush); zone 5 Sun 03:00 = 0; sampled Friday
  arrivals zone 161 = 4,691.

## Decisions / deviations from plan
- `arrival_rate` returns riders **per minute** (spec §4 wording); `sample_arrivals`
  works in minutes internally.

## Blocked / deferred
- none.

## Next
- M4 entities-city — `entities.py` (Rider/Driver state machines) + `city.py`
  (`CityModel.build`) + `configs/sim/baseline.yaml`.
