# ADR-0001: Data pipeline — DuckDB cleaning, pandera gates, Repository seam

**Status:** accepted
**Date:** 2026-08-28
**Context:** Plan Stage 1 (`data` package). Spec §4 (`data`), §5 (Data), §8
(Repository pattern), §10 (fail loudly).

## Decision

### 1. DuckDB for out-of-core cleaning; pandas only for the dense grid

Raw yellow-taxi months are ~3 M rows each. Row filtering (month bounds, duration,
distance, zone range, dedupe) runs entirely as DuckDB SQL over `read_parquet`,
and the result is written with `COPY ... TO parquet`. A full month is never held
in a pandas frame during cleaning.

pandas *is* used where the data is already small: the demand feature grid is
263 zones × ~1,416 hours ≈ 372 k rows, and lag / rolling-window features are far
easier to express correctly (and to prove leak-free) with `groupby().shift()`
than in SQL window functions.

**Alternatives considered:**
- *pandas chunking* — manual chunk loops are error-prone and slow; DuckDB does
  predicate pushdown for free.
- *Polars* — capable, but DuckDB's SQL is a better fit for ad-hoc aggregation and
  is already the spec's stated tool (§9).
- *A warehouse (BigQuery/Snowflake)* — out of scope; the project is deliberately
  local-first (spec §2).

### 2. pandera schemas are the loud gate

`RawYellowTripSchema`, `CleanedTripSchema`, `DemandFeatureSchema`,
`EtaFeatureSchema` (`src/ridepulse/data/schemas.py`). Each stage validates its
output before it is trusted; a violation raises and the CLI exits non-zero
(spec §10). Feature/cleaned schemas are `strict=True` (no surprise columns); the
raw schema is `strict=False` (raw files carry many fare columns we ignore).
`passenger_count` is nullable `Int64` — real data has ~2 % nulls, kept.

### 3. Repository pattern over the processed store

`ParquetRepository` maps logical names (`cleaned_trips`, `demand_features`,
`eta_features`) to paths. Consumers never build paths. Changing the on-disk
layout touches only `_REGISTRY`. `read` on an unbuilt dataset raises
`FileNotFoundError`; an unknown name raises `KeyError`.

## Cleaning rules (recorded as modeling assumptions)

| Rule | Rationale |
| --- | --- |
| pickup timestamp within the target month | TLC monthly files contain a tail of stray prior/next-month rows; dropping them keeps month partitions clean. |
| `duration_min` in (0, 180] | ≤ 0 is a clock/logging error; > 3 h is implausible for a metered NYC taxi trip and dominated by meter-left-running noise. |
| `trip_distance` in (0, 100] miles | 0 is missing/void; > 100 mi is outside the service area (data artefacts). |
| `PU/DOLocationID` in 1..263 | 264 ("Unknown") and 265 ("Outside of NYC") carry no usable geography; nulls likewise dropped. |
| exact-duplicate rows collapsed | occasional double-logging in the source; `SELECT DISTINCT` on the emitted columns. |

Consequence: the cleaned table is a *analysis sample*, not the full ledger.
Roughly 96 % of raw rows survive (2023-01: 2.95 M of ~3.07 M).

## Consequences

- Deterministic: same inputs → identical row counts and content on re-run.
- The one place a month enters pandas is the post-clean re-read for
  `CleanedTripSchema.validate` (~1 s / 3 M rows) — acceptable on 8 GB.
- Weather, green-taxi, FHV, and months beyond 2023-02 are deferred increments
  (plan "Deferred increments").
