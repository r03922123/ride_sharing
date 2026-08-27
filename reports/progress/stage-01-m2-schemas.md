# Stage 1 — M2 schemas

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (6 files) · pytest 21 passed

## Done
- `src/ridepulse/data/schemas.py` — four pandera `DataFrameSchema`s:
  - `RawYellowTripSchema` — `strict=False` (raw files carry unused fare columns);
    validates pickup/dropoff datetimes, `passenger_count` (nullable), `trip_distance`,
    `PU/DOLocationID`.
  - `CleanedTripSchema` — `strict=True`; `pu/do_location_id` in 1..263,
    `trip_distance` in (0, 100], `duration_min` in (0, 180], `passenger_count` ≥ 0.
  - `DemandFeatureSchema` — `zone_id` 1..263, `pickups` ≥ 0, `hour` 0..23,
    `dow` 0..6, `is_holiday` bool, nullable lag/rolling columns (warmup NaN).
  - `EtaFeatureSchema` — zone pair, `hour`, `dow`, positive `trip_distance`,
    `duration_min` in (0, 180].
- `tests/data/test_schemas.py` — good rows accepted; rejects wrong dtype,
  out-of-range zone (300), non-positive duration, extra columns, `hour=24`,
  zero distance; confirms nullable lags accepted.

## Decisions / deviations from plan
- Per-column `coerce=True` only (no schema-level `coerce`) so pandera raises a
  consistent error type. Tests accept `(SchemaError, SchemaErrors)` since pandera
  raises the plural form for coercion failures.
- Zone range fixed at 1..263 (the real zones); 264/265 "Unknown" are dropped by
  cleaning in M3, recorded as a modeling assumption in the data dictionary.

## Blocked / deferred
- none.

## Next
- M3 clean — `data/clean.py` (`clean_month`, DuckDB SQL only) + ~40-row raw
  fixture, one row per cleaning rule; pandera-validate output.
