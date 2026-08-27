# Stage 1 — M7 cli-wire

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (11 files) · pytest 40 passed

## Done
- `src/ridepulse/data/pipeline.py` — orchestration:
  - `parse_months("2023-01..2023-03")` → `["2023-01","2023-02","2023-03"]`
    (year rollover handled; reversed range → `ValueError`).
  - `download_sources`, `clean_months` (per-month `clean_month` → DuckDB concat
    into `cleaned_trips`), `build_features` (demand + eta), `build_all`.
  - No error handling — schema violations propagate so the CLI exits non-zero.
- `src/ridepulse/cli.py` — `data` sub-app: `download`, `clean`, `features`,
  `build`, `validate`. Option factories hoisted to module level (ruff B008).
- `Makefile`: `data:` → `uv run ridepulse data build --months 2023-01..2023-02`.
- `tests/data/test_pipeline.py` — `parse_months` cases; clean→features→validate
  end-to-end on a tmp raw fixture via `CliRunner`; **fail-loud test**: a
  `cleaned_trips` parquet with `pu_location_id=999` makes `data features` exit
  non-zero.

## Real end-to-end (`make data`, `data/processed/` gitignored)
- `ridepulse data build --months 2023-01..2023-02`: **`data build complete`**.
  - `demand_features.parquet`: **372,408 rows** = 263 zones × 1,416 hours
    (Jan 744 + Feb 672) — matches the plan's expected shape.
  - `eta_features.parquet`: **5,747,294 rows**, train 4,597,835 / holdout
    1,149,459 (80/20).
  - Re-run row counts identical (deterministic SQL + feature build).

## Decisions / deviations from plan
- Per-month cleaned parts land in `data/processed/_months/` (gitignored) before
  the DuckDB concat into `cleaned_trips`.

## Blocked / deferred
- none.

## Next
- M8 docs-pr — `docs/adr/0001-data-pipeline-and-repository.md`,
  `docs/data-dictionary.md`; final full gate; open PR.
