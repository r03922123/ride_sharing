# Data dictionary — `data` package outputs

Three parquet tables, all written via `ParquetRepository` under
`<root>/processed/`. Built by `ridepulse data build --months 2023-01..2023-02`.

Source: NYC TLC yellow-taxi trip records (`manifests/tlc_2023.yaml`,
SHA-256-pinned). Scope for this stage: 2023-01 and 2023-02 only.

---

## `cleaned_trips`

One row per valid trip after the §"Cleaning rules" filters (ADR-0001).

| Column | Dtype | Semantics | Null policy |
| --- | --- | --- | --- |
| `pickup_ts` | `datetime64[ns]` | Trip start (TLC `tpep_pickup_datetime`). Within the target month. | never null |
| `dropoff_ts` | `datetime64[ns]` | Trip end (TLC `tpep_dropoff_datetime`). | never null |
| `pu_location_id` | `int64` | Pickup taxi zone, 1..263. | never null |
| `do_location_id` | `int64` | Drop-off taxi zone, 1..263. | never null |
| `trip_distance` | `float64` | Metered miles, in (0, 100]. | never null |
| `passenger_count` | `Int64` (nullable) | Driver-entered passenger count, ≥ 0. | null kept (~2 % of rows) |
| `duration_min` | `float64` | `(dropoff_ts − pickup_ts)` in minutes, in (0, 180]. | never null |

Row count ≈ 96 % of raw (2023-01: 2,945,217 of ~3.07 M).

---

## `demand_features`

One row per `(zone, hour)` on a **dense zero-filled grid**: every zone 1..263 ×
every hour in the observed range (2023-01..02 → 1,416 hours → 372,408 rows).
Target column: `pickups`.

| Column | Dtype | Semantics | Null policy |
| --- | --- | --- | --- |
| `zone_id` | `int64` | Taxi zone, 1..263. | never null |
| `ts` | `datetime64[ns]` | Hour bucket (`date_trunc('hour', pickup_ts)`). | never null |
| `pickups` | `int64` | Trips starting in this zone during this hour (**target**). 0 where none. | never null |
| `hour` | `int64` | Hour of day, 0..23. | never null |
| `dow` | `int64` | Day of week, Monday=0..Sunday=6. | never null |
| `is_holiday` | `bool` | US federal holiday (observed) on `ts`'s date. | never null |
| `lag_1h` | `float64` | `pickups` at `ts − 1h`, same zone. | null in the first 1 h per zone |
| `lag_24h` | `float64` | `pickups` at `ts − 24h`, same zone. | null in the first 24 h per zone |
| `lag_168h` | `float64` | `pickups` at `ts − 168h`, same zone. | null in the first 168 h per zone |
| `roll_mean_24h` | `float64` | Mean of the **strictly-past** ≤ 24 `pickups` values, same zone. | null in the first 1 h per zone |
| `roll_mean_168h` | `float64` | Mean of the strictly-past ≤ 168 `pickups` values, same zone. | null in the first 1 h per zone |

**Leakage guarantee:** every lag / rolling column at `ts` is derived from
`pickups` values strictly before `ts` (`shift(1)` before any window). Asserted in
`tests/data/test_features_demand.py`.

---

## `eta_features`

One row per cleaned trip. Target column: `duration_min`.

| Column | Dtype | Semantics | Null policy |
| --- | --- | --- | --- |
| `pickup_ts` | `datetime64[ns]` | Trip start (kept for the time-ordered split). | never null |
| `pu_location_id` | `int64` | Pickup zone, 1..263. | never null |
| `do_location_id` | `int64` | Drop-off zone, 1..263. | never null |
| `hour` | `int64` | Pickup hour of day, 0..23. | never null |
| `dow` | `int64` | Pickup day of week, Monday=0..Sunday=6. | never null |
| `trip_distance` | `float64` | Metered miles, > 0. | never null |
| `passenger_count` | `Int64` (nullable) | ≥ 0. | null kept |
| `duration_min` | `float64` | `(dropoff_ts − pickup_ts)` minutes, in (0, 180] (**target**). | never null |
| `split` | `str` | `"train"` (earliest 80 % by `pickup_ts`) or `"holdout"` (latest 20 %). | never null |

**Split guarantee:** `max(pickup_ts where split='train') < min(pickup_ts where
split='holdout')` — no shared timestamp. Asserted in
`tests/data/test_features_eta.py`.

---

## Conventions

- `dow`: Monday=0..Sunday=6 (pandas `dayofweek`). DuckDB's Sunday=0 output is
  remapped in `features_eta`.
- All timestamps are naive local time as published by TLC (America/New_York); no
  timezone conversion is applied.
- Parquet written with `index=False`.
