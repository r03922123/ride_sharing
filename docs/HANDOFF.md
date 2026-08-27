# Handoff

**Last updated:** 2026-08-27
**Branch:** `main` (clean sync point — see spec §17, the repo is the only channel
between the M1 and any remote)

---

## Where the project is

Design phase is complete. Implementation of Phase 0 + Phase 1 is **planned but not
started** — no `src/` code exists yet.

| Artifact | Path | State |
| --- | --- | --- |
| Design spec | `docs/superpowers/specs/2026-08-27-ride-sharing-ml-portfolio-design.md` | Approved, committed |
| Phase 0+1 implementation plan | `docs/superpowers/plans/2026-08-27-ride-pulse-phase-0-1-implementation.md` | Ready to execute |
| Devcontainer / README / gitignore | repo root, `.devcontainer/` | Committed |
| `src/ridepulse/` package | — | Does not exist yet |

---

## What was done this session

1. Read the full design spec.
2. Produced the **Phase 0 + Phase 1 implementation plan**
   (`docs/superpowers/plans/2026-08-27-ride-pulse-phase-0-1-implementation.md`),
   scoped to: data pipeline, `sim.core`, `sim.des` (+ `sim.mdp` stub), and the
   forecasting service. Structured as **7 stacked per-package PRs**, each
   mergeable with green CI + an ADR:

   | Stage | Package | Ends with |
   | --- | --- | --- |
   | 0 | scaffold | `uv`/`pyproject`, ruff+mypy+pytest+pre-commit, `Makefile`, CI green |
   | 1 | `data` | `make data` reproduces demand + ETA feature tables from a checksummed manifest |
   | 2 | `sim.core` | calibrated city model + the core/des/mdp-split ADR |
   | 3 | `sim.des` | scenario run emits an event log; conservation invariants green → **spec Phase 0 Done** |
   | 4 | `forecast` | leakage-asserted rolling-origin backtest, conformal intervals, MLflow registry |
   | 5 | `serving` | FastAPI `/forecast` with intervals, Dockerized, load test recorded |
   | 6 | integration | `make smoke` in CI; README + skills-map → **spec Phase 1 Done** |

3. Recorded that the **superpowers plugin is not installed in this Codespace** —
   the `writing-plans` skill could not be invoked, so the plan was written by
   hand in the same house style. (Saved to agent memory.)

---

## Decisions made this session

Full rationale is in the plan's decision table (§"Planning decisions"). Summary:

| # | Decision |
| --- | --- |
| D1 | Phase 0–1 data scope = **yellow taxi only, 2023-01..2023-02**, built in the Codespace. Green + FHV + full 6 months are a deferred increment for the M1 / Oracle box. |
| D2 | **Weather feature deferred.** Phase 1 model = calendar + lags + rolling means only; `precip × hour` becomes a later before/after-backtest increment. |
| D3 | **One stacked PR per package**, not one PR per phase. |
| D4 | `src/ridepulse/` import package (repo dir stays `ride_sharing`); `uv` + `pyproject.toml`; ruff + mypy + pytest + pre-commit and CI from Phase 0; E2E smoke job added in Phase 1. |
| D5 | Baseline `DispatchPolicy` = **nearest idle driver within radius, else FIFO queue**. |
| D6 | CLI framework = **`typer`**, single `ridepulse` console script with `data` / `sim` / `forecast` / `serve` sub-apps. |
| D7 | Zone spatial model = **zone-centroid distance matrix, precomputed once and committed**; `geopandas` / `shapely` in an optional `geo` extra, not a runtime dep. |
| D8 | Demand calibration = Poisson **rate per (zone × hour-of-week)** from cleaned trips. |
| D9 | Backtest folds = **expanding window, weekly test folds** (2 months is too thin for the spec's monthly folds). Revisit when full data lands. |
| D10 | Prediction intervals = **split-conformal** for the reported interval; native LightGBM quantile models fit and reported alongside for comparison. |

Still open (not blockers for Phase 0–1): Phase 4a intervention choice; risk-label
source; HF Space envelope; `sim.mdp` state resolution (all resolved later per
spec §16).

---

## What's next

**Start Stage 0 (scaffold)** from the plan. Create a branch, work the task list
top to bottom (tests first), get CI green, open the PR. Then Stage 1 (`data`)
branches off Stage 0, and so on.

The plan's "How to execute" section has the branch-per-stage workflow. Each
stage's "Mergeable when" is the gate.
