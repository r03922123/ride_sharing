# Autonomous work block — 2026-08-28

**Mode:** unattended, ~4 hours, permission prompts skipped (user commuting).
**Branch:** `stage/01-data` (off `main` @ `6a711aa`).
**Scope:** Plan Stage 1 (`data` package). If it finishes with time/budget left,
start Stage 2 (`sim.core`) on `stage/02-sim-core` — do **not** exceed Stage 2.
**Source of truth:** `docs/superpowers/plans/2026-08-27-ride-pulse-phase-0-1-implementation.md`.

## Operating rules

1. **TDD per task**: write the test, run it red, implement, run it green.
2. **Token economy** (weekly limit is a real risk):
   - Run *targeted* tests (`pytest tests/data/test_x.py -q`), not the full suite,
     until a milestone boundary.
   - One combined `ruff check . && mypy src && pytest -q` gate per milestone only.
   - Do not re-read files already in context. Keep reports terse.
3. **Checkpoint every milestone**:
   - `ruff check . && mypy src && pytest -q` must pass.
   - `git add -A && git commit` with a clear message.
   - Write `reports/progress/stage-01-mNN-<slug>.md` (template below).
   - `git push` (branch) roughly every 2 milestones.
4. **Never leave the tree broken across a commit.** If a task can't be completed,
   revert that task's partial changes, record it under "Blocked" in the milestone
   report, and move to the next independent task.
5. **Real data download** (M1 milestone): attempt the real NYC TLC download once.
   If it fails (network/size/blocked), continue with committed fixtures, leave
   `sha256: null` in the manifest, and flag it in the report — do not block.
6. **No scope creep**: only files the plan's Stage 1 (then Stage 2) task list names.
   No `eta`/`risk`/`agent`/`serving` work. No weather. Yellow-taxi 2023-01..02 only.
7. **If interrupted** (token limit / laptop sleep): the last committed milestone +
   its report is the resume point. `git log` + newest `reports/progress/*.md` say
   exactly where to continue.

## Milestones (Stage 1)

| # | Slug | Deliverable | Key tests |
|---|---|---|---|
| M1 | manifest-download | `data/manifest.py`, `data/download.py`, `manifests/tlc_2023.yaml`, fixture manifest; attempt real download + fill checksums | `test_manifest.py`, `test_download.py` (checksum verify, wrong-checksum raises, resume) |
| M2 | schemas | `data/schemas.py` — `RawYellowTripSchema`, `CleanedTripSchema`, `DemandFeatureSchema`, `EtaFeatureSchema` | `test_schemas.py` (good accepted, bad rejected) |
| M3 | clean | `data/clean.py` (`clean_month`, DuckDB SQL only), ~40-row raw fixture, pandera-validated output | `test_clean.py` (one row per cleaning rule) |
| M4 | features-demand | `data/features_demand.py` (`build_demand_features`); dense zero-filled zone×hour grid; calendar + lags + rolling means; **leakage assertion** | `test_features_demand.py` |
| M5 | features-eta | `data/features_eta.py` (`build_eta_features`); `duration_min`; time-ordered split no overlap | `test_features_eta.py` |
| M6 | repository | `data/repository.py` (`ParquetRepository`, logical-name registry) | `test_repository.py` (round-trip, unknown name raises) |
| M7 | cli-wire | `ridepulse data build --months 2023-01..2023-02` + sub-commands; `Makefile` `data:` target; fail-loud test | `test_pipeline_fails_loud.py` |
| M8 | docs-pr | `docs/adr/0001-data-pipeline-and-repository.md`, `docs/data-dictionary.md`; final full gate; push; open PR if `gh` present | full `pytest`, `ruff`, `mypy` |

**Stage 1 mergeable when:** CI-equivalent gate green; ADR-0001 + data dictionary present.

## Milestone report template

```
# Stage 1 — M<NN> <slug>

**Commit:** <sha>
**Status:** done | partial
**Gate:** ruff <pass/fail> · mypy <pass/fail> · pytest <n passed / n failed>

## Done
- <bullet per task completed, with the test that guards it>

## Decisions / deviations from plan
- <any; "none" if none>

## Blocked / deferred
- <task + reason + what a human needs to decide; "none" if none>

## Next
- M<NN+1> <slug>
```

## Final wrap (write `reports/progress/stage-01-SUMMARY.md`)

- Table of all milestones + commit shas + gate results.
- Whether `make data` on real data succeeded and the resulting row counts.
- Open questions for user review.
- If Stage 2 was started: same milestone log under a Stage 2 heading.
