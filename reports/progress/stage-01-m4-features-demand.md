# Stage 1 — M4 features-demand

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (8 files) · pytest 28 passed

## Done
- `src/ridepulse/data/features_demand.py` — `build_demand_features(cleaned_path, out_path)`:
  - DuckDB aggregates cleaned trips → hourly `(ts, zone_id, pickups)`.
  - `_dense_grid`: reindex onto the full `MultiIndex(zone 1..263 × every hour in
    range)`, `fill_value=0` → dense zero-filled grid.
  - `_add_calendar`: `hour`, `dow`, `is_holiday` (US holidays via
    `holidays.country_holidays`).
  - `_add_lags_and_rolls`: per-zone `shift(k)` for `lag_1h/24h/168h`;
    rolling means computed on `shift(1)` first → **row `t` uses only `< t`**.
  - `DemandFeatureSchema.validate(..., lazy=True)` before writing parquet.
- `tests/data/test_features_demand.py` — 5 tests:
  - dense grid densifies to all 263 zones × N hours; empty zone present & all-zero.
  - pickup counts match the deterministic `(zone+hour)%4` fixture.
  - calendar columns; New Year's Day observed = 2023-01-02 flagged `is_holiday`.
  - **leakage assertion**: `lag_1h[i] == pickups[i-1]` (never `[i]` or later);
    `lag_24h[i] == pickups[i-24]`; warmup entries NaN.
  - rolling means equal `mean(pickups[max(0,i-24):i])` — strictly past.

## Real-data smoke (`data/processed/` gitignored)
- `build_demand_features` on cleaned 2023-01: **195,672 rows** (263 zones × 744
  hours), 0.3 s, schema-valid. pickups mean 15.05, max 690. lag_1h warmup NaN =
  263 (one per zone). zone 161 hour-1/2 lag_1h = 184, 162 — plausible Midtown.

## Decisions / deviations from plan
- Fixture spans 26 hours (plan said "12") so `lag_24h` has checkable non-null
  values; `lag_168h` asserted all-NaN at this span.
- Added dev dep `pandas-stubs` for mypy strict.

## Blocked / deferred
- none.

## Next
- M5 features-eta — `data/features_eta.py`, `duration_min`, time-ordered
  train/holdout split with no timestamp overlap.
