# Stage 1 (`data` package) — SUMMARY

**Branch:** `stage/01-data` (off `main` @ `6a711aa`) — pushed, **not yet merged**.
**Result:** all 8 milestones done. `make data` reproduces the demand + ETA
feature tables from a SHA-256-pinned manifest. 40 tests green; ruff + mypy
`--strict` clean. Ready for PR + merge.

## Milestones

| # | Slug | Commit | Gate |
| --- | --- | --- | --- |
| M1 | manifest-download | `b1972f6` | ruff·mypy·15 tests |
| M2 | schemas | `1c… (see log)` | ruff·mypy·21 tests |
| M3 | clean | `30ad9b3` | ruff·mypy·23 tests |
| M4 | features-demand | `c5b5576` | ruff·mypy·28 tests |
| M5 | features-eta | `87a80a8` | ruff·mypy·32 tests |
| M6 | repository | `a25885b` | ruff·mypy·37 tests |
| M7 | cli-wire | `718ce8c` | ruff·mypy·40 tests |
| M8 | docs-pr | (this commit) | ruff·mypy·40 tests |

(Exact shas: `git log --oneline main..stage/01-data`.)

## `make data` on real data (2023-01..2023-02, yellow only)

| Table | Rows | Shape |
| --- | --- | --- |
| `cleaned_trips` | 5,747,294 | ~96 % of raw survive the cleaning filters |
| `demand_features` | 372,408 | 263 zones × 1,416 hours, dense zero-filled |
| `eta_features` | 5,747,294 | train 4,597,835 / holdout 1,149,459 (80/20, no ts overlap) |

Re-run row counts identical (deterministic).

## What exists now

```
src/ridepulse/data/
  manifest.py        Manifest / ManifestEntry / load_manifest
  download.py        sha256 verify, ChecksumMismatch, resumable fetch, fetch_all
  schemas.py         Raw / Cleaned / DemandFeature / EtaFeature pandera schemas
  clean.py           clean_month  (DuckDB SQL only + pandera gate)
  features_demand.py build_demand_features  (dense grid, leakage-safe lags)
  features_eta.py    build_eta_features  (time-ordered train/holdout split)
  repository.py      ParquetRepository  (logical-name -> path seam)
  pipeline.py        parse_months, clean_months, build_features, build_all
cli.py               data sub-app: download / clean / features / build / validate
docs/adr/0001-data-pipeline-and-repository.md
docs/data-dictionary.md
```

## Open questions for review

1. **`EtaFeatureSchema` gained `pickup_ts` + `split`** (plan M2 listed neither) —
   needed for the holdout boundary. OK to keep in the schema, or move `split`
   out to a sidecar?
2. **Cleaning thresholds** (duration ≤ 180 min, distance ≤ 100 mi) are round
   numbers, not data-driven percentiles. Fine for now; revisit with the full-data
   increment?
3. **Fixture spans** — demand fixture is 26 h (plan said 12) to make `lag_24h`
   testable; `lag_168h` only gets structural (all-NaN) coverage until real data.
4. `gh` absent on the M1 → **PR must be opened manually** from GitHub.

## Next (per plan)

**Stage 2 — `sim.core`** on `stage/02-sim-core` (branch off `stage/01-data`
once merged, or off its head): `scripts/build_zone_geometry.py` (needs `geo`
extra), `grid.py`, `zones.py`, `demand.py` (Poisson (zone × hour-of-week)
calibration), `entities.py`, `city.py`, ADR-0002 (the core/des/mdp-split ADR) +
`docs/lld/sim-class-diagram.md`. Not started.
