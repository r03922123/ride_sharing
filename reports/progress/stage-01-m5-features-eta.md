# Stage 1 — M5 features-eta

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (9 files) · pytest 32 passed

## Done
- `src/ridepulse/data/features_eta.py` — `build_eta_features(cleaned_path, out_path)`:
  DuckDB select of PU/DO zone, pickup `hour`, `dow` (DuckDB Sun=0 remapped to
  Mon=0..Sun=6), `trip_distance`, `passenger_count`, `duration_min` (target);
  `_time_split` labels the last 20% of trips by pickup time `holdout` with a
  strict cutoff so **train and holdout share no timestamp**;
  `EtaFeatureSchema.validate(..., lazy=True)` then parquet.
- `EtaFeatureSchema` gained `pickup_ts` and `split` columns (needed for the
  holdout boundary and for downstream backtest wiring).
- `tests/data/test_features_eta.py` — 4 tests: exact column list; `duration_min`
  equals `(dropoff - pickup)` minutes; `hour`/`dow` of the first trip;
  **`train.pickup_ts.max() < holdout.pickup_ts.min()`** and holdout size = 20%.

## Real-data smoke (`data/processed/` gitignored)
- `build_eta_features` on cleaned 2023-01: **2,945,217 rows**, 3.2 s, schema-valid.
  train 2,356,173 / holdout 589,044, **no timestamp overlap = True**. duration
  mean 14.41 min; `dow` covers 0..6.

## Decisions / deviations from plan
- `EtaFeatureSchema` extended with `pickup_ts` + `split` (M2 listed neither).
- `dow` convention pinned to Monday=0 (matches pandas `dayofweek` used in the
  demand table) — DuckDB `dayofweek` is Sunday=0, remapped in code.

## Blocked / deferred
- none.

## Next
- M6 repository — `data/repository.py` (`ParquetRepository`, logical-name →
  path registry) + round-trip test.
