# Stage 1 — M3 clean

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (7 files) · pytest 23 passed

## Done
- `src/ridepulse/data/clean.py` — `clean_month(raw_path, month, out_path)`:
  DuckDB SQL only (no full month in pandas), `COPY ... TO parquet`, then reads the
  result back once and runs `CleanedTripSchema.validate(df, lazy=True)` as the
  loud gate.
  Rules: pickup in target month; `duration_min` in (0, 180]; `trip_distance` in
  (0, 100]; `pu/do_location_id` in 1..263 (drops 264/265/null); exact-duplicate
  rows collapsed (`SELECT DISTINCT`).
- `tests/data/test_clean.py` — 17-row hand-built raw fixture, one row per rule;
  asserts the 7 survivors, every range, month bounds, dedup (zone-42 trip appears
  once), null `passenger_count` preserved. Second test asserts the internal
  schema validation passes.
- Schema fix: `passenger_count` is `Column("Int64", ...)` (pandas nullable) in
  `CleanedTripSchema` + `EtaFeatureSchema`; DuckDB casts ids/pax to `BIGINT` so
  `.df()` yields nullable `Int64` and coercion never drops NA.

## Real-data smoke (not committed — `data/processed/` is gitignored)
- `clean_month` on real `yellow_tripdata_2023-01.parquet`: **2,945,217** cleaned
  rows (from ~3.07 M raw), **1.3 s**, pandera-valid. pu id range 1..263, duration
  0.02..179.6 min, 63,611 null passenger counts retained.

## Decisions / deviations from plan
- Output validation reads the cleaned parquet back into one pandas frame (~3 M
  rows, ~1 s). This is the only place a month touches pandas; the *filtering* is
  pure DuckDB per the plan. Acceptable on 8 GB.

## Blocked / deferred
- none.

## Next
- M4 features-demand — `data/features_demand.py`, dense zone×hour grid, calendar +
  lags + rolling means, **leakage assertion** in the test.
