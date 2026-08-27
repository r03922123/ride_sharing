# Autonomous roadmap — Stages 2–6 (2026-08-28)

**Mode:** fully unattended. A senior agent owns every decision, self-review, and
merge. No human gate anywhere. ~4-hour block, weekly-token-limit aware.
**Start point:** `stage/01-data` @ `b57022e` (Stage 1 complete, not yet merged).
**Source of truth:** `docs/superpowers/plans/2026-08-27-ride-pulse-phase-0-1-implementation.md`
(Stages 2–6) + the design spec.

---

## 0. Standing authority (what "manual → agent responsibility" means)

The agent does NOT ask. For anything the plan does not pin:

1. Follow the plan's locked decisions D1–D10 verbatim.
2. Where the plan is silent, choose the option that — in order — (a) minimises
   scope, (b) best matches spec intent, (c) is most defensible in a portfolio
   review. Record it as a new `Dxx` in the stage report; add/extend an ADR if it
   is architectural.
3. Never block, never leave a `TODO` for a human. If a choice is consequential
   and genuinely close, take the conservative option and list it under
   "decisions made autonomously — reverse if you disagree" in the final SUMMARY.
4. Self-review replaces PR review. For every stage, answer the spec §8 questions
   in the stage report ("can a consumer understand this package without reading
   its internals? can the internals change without breaking consumers?") and the
   plan's "Mergeable when" checklist. If the answer is no, refactor before merge.

### Stage-1 open questions — resolved here

- **`EtaFeatureSchema` carries `pickup_ts` + `split`** → keep. Defensible; the
  split boundary needs `pickup_ts`. Resolved, no change.
- **Cleaning thresholds (180 min / 100 mi)** → keep as fixed constants for this
  data scope; logged as a tunable in the deferred-increments list. Resolved.
- **PR flow** → `gh` is unavailable. Replace with local no-ff self-merge
  (below). Resolved.

## 1. Merge model (no `gh`)

Each stage: branch `stage/0N-<slug>` off the previous stage's merge commit on
`main`. When the stage gate is green and the self-review passes:

```
git switch main
git merge --no-ff stage/0N-<slug> -m "Merge Stage N: <slug>"
git push
git switch -c stage/0(N+1)-<slug>
```

`main` stays releasable at every merge. Never merge a red stage.

## 2. Operating rules (unchanged from the Stage-1 block)

- **TDD per task:** test first (red), implement (green).
- **Token economy:** targeted `pytest tests/<pkg>/test_x.py` during a milestone;
  one combined `ruff check . && mypy src && pytest -q` gate at the milestone
  boundary only. No re-reading files already in context. Terse reports.
- **Checkpoint every milestone:** gate green → `git commit` → write
  `reports/progress/stage-0N-mMM-<slug>.md` (template in the Stage-1 roadmap) →
  `git push` roughly every 2 milestones.
- **Never leave the tree broken across a commit.** A task that cannot complete:
  revert its partial changes, record under "Blocked" with the concrete reason,
  move to the next independent task.
- **Tool unavailable** (e.g. Docker daemon not running): build everything that
  does not need it, run the app-level tests (`fastapi.testclient`), mark the
  tool-gated verification "deferred: <tool> unavailable in autonomous env" in the
  report, and continue — do not block the stage.
- **No scope creep:** only files the plan's stage task list names. No `eta`
  model, `risk`, `agent`, `eval`, `monitoring`. No RL. No weather. Yellow-taxi
  2023-01..02 only.

## 3. Hard-stop protocol

If the token budget looks near exhaustion, or ~4h elapsed, or 3 consecutive
milestones fail their gate:

1. Finish the current milestone to green **or** revert it fully.
2. Commit + push whatever is green.
3. If a whole stage is green but unmerged, self-merge it to `main`.
4. Write `reports/progress/STAGES-2-6-SUMMARY.md` (running log, updated after
   every stage; on stop it is the resume handoff).
5. Stop. Do not start a new milestone.

**Acceptable stop points** (each leaves a coherent deliverable):
- End of **Stage 3** → spec §14 **Phase 0 Done** (`sim.des` runs, invariants green).
- End of **Stage 5** → the `/forecast` API is live.
- End of **Stage 6** → spec §14 **Phase 1 Done** (one-command clone→forecast).

## 4. Stage milestones

### Stage 2 — `sim.core`  (branch `stage/02-sim-core`)
| M | slug | deliverable |
|---|---|---|
| 1 | zone-geometry | `scripts/build_zone_geometry.py` (`geo` extra) → commit `zone_centroids.parquet` + `zone_distances.npy`; `grid.py` (`CityGrid.load/.distance_km/.travel_time_min`) + tests (symmetry, diagonal 0, monotone travel time) |
| 2 | zones | `zones.py` (`ZoneMap.load`) + tests (263 load, id↔name↔borough round-trip, out-of-range raises) |
| 3 | demand | `demand.py` (`DemandProfile.calibrate` → (zone × hour-of-week) Poisson table artifact; `.from_artifact`; `.arrival_rate`; `.sample_arrivals`) + tests (non-negative/finite all week; daily total within ±15% of real mean for a sample zone; seed-deterministic) + CLI `ridepulse sim calibrate` |
| 4 | entities-city | `entities.py` (`Rider`/`Driver` state machines, `Assignment`) + `city.py` (`CityModel.build`, `CityConfig`) + tests (legal/illegal transitions; deterministic build); `configs/sim/baseline.yaml` |
| 5 | adr-merge | ADR-0002 (core/des/mdp split — full justification per plan) + `docs/lld/sim-class-diagram.md` (mermaid, core entities); §8 self-review in report; full gate; **self-merge to main** |

### Stage 3 — `sim.des` (+ `sim.mdp` stub)  (branch `stage/03-sim-des`)
| M | slug | deliverable |
|---|---|---|
| 1 | events | `sim/des/events.py` (event dataclasses, `EventLog` parquet round-trip) + tests |
| 2 | dispatch | `sim/des/dispatch.py` (`DispatchPolicy` ABC, `NearestDriverPolicy` = nearest idle within `radius_km` else FIFO, `POLICIES` registry) + tests (closest assigned, no double-assign, unmatched served FIFO) |
| 3 | observers | `sim/des/observers.py` (`EventObserver` ABC, `MetricsCollector`, `EventLogWriter`) + `metrics.py` (`summarize`) + tests (collector totals == recompute from raw log) |
| 4 | simulation | `sim/des/simulation.py` (`Simulation(config).run()->EventLog`; SimPy env; Poisson arrivals; rider lifecycle; driver movement) + tests (tiny scenario runs, **byte-identical event frame on seed re-run**) |
| 5 | invariants-stub | `tests/sim/des/test_invariants.py` (conservation: one terminal state per rider, constant driver count, no dual state, no dropoff before pickup, matched⇒idle-at-match); `sim/mdp/interface.py` stub (`NotImplementedError`); `tests/sim/test_des_mdp_consistency.py` **written + `@pytest.mark.skip`**; CLI `ridepulse sim run`; Makefile `sim:` |
| 6 | adr-merge | extend ADR-0002 / add ADR-0003 (Strategy for `DispatchPolicy`, Observer for events); extend class diagram; §8 self-review; full gate; **self-merge to main** → *Phase 0 Done* |

### Stage 4 — `forecast`  (branch `stage/04-forecast`)
| M | slug | deliverable |
|---|---|---|
| 1 | dataset | `forecast/dataset.py` (`assemble` → aligned X/y/ts, drop lag-warmup NaN rows) + tests |
| 2 | backtest-leakage | `forecast/backtest.py` — `RollingOriginBacktest`, **`LeakageError` guard** (`max(train_ts) < min(test_ts)` per fold; overlapping spec raises); expanding weekly folds; `score_fold` MAE/MAPE/bias matching Appendix A.1 hand values + tests |
| 3 | intervals | `forecast/intervals.py` (`SplitConformal.calibrate/.interval`); `coverage_report` matching Appendix A.3 (612/720 → +5.0pp pass; +7pp fail) + tests |
| 4 | model | `forecast/model.py` (`ForecastModel` Protocol, `BaseForecaster` Template-Method, `LightGBMForecaster` global model + conformal interval + q0.1/q0.9 comparison); `baselines.py` (`SeasonalNaiveForecaster` = value 168h earlier) + tests (deterministic, `lower≤point≤upper`) |
| 5 | registry-report | `forecast/registry.py` (mlflow local file backend: `log_model/load/promote`) + tests (round-trip, promote to Production); `forecast/report.py` (`write_backtest_report` → methodology.md/metrics.json/folds.csv/PNG) + tests; `configs/forecast/*.yaml`; CLI `forecast train` / `forecast backtest`; Makefile `train:`/`backtest:` |
| 6 | adr-merge | ADR-0004 (ForecastModel Protocol/Template-Method, split-conformal rationale, registry behind Repository seam); run `make backtest` on real data → commit `reports/backtest/`; §8 self-review; full gate; **self-merge to main** |

### Stage 5 — `serving`  (branch `stage/05-serving`)
| M | slug | deliverable |
|---|---|---|
| 1 | schemas-routes | `serving/schemas.py` (`ForecastRequest`/`Response`, validation → 422); `serving/app.py` (`create_app`), `routes.py` (`/forecast`, `/healthz`; empty registry → 503) + tests (`fastapi.testclient`) |
| 2 | middleware-logging | `serving/middleware.py` (unique `request_id`, `latency_ms`); `serving/logging.py` (one JSON line/request with request_id/zone_id/latency_ms/model_version/status) + tests |
| 3 | contract-loadtest | `tests/serving/test_contract.py` vs committed `docs/openapi/forecast.json`; `serving/loadtest/locustfile.py` + `run_loadtest.sh` → `reports/loadtest/forecast.md` (p50/p90/p99, p99 idx = ceil(0.99·n), PASS/FAIL vs 100ms — either outcome OK) |
| 4 | docker-merge | `serving/Dockerfile`, `docker-compose.yml` (serving svc, healthcheck); CLI `ridepulse serve`; Makefile `serve:`/`loadtest:`; ADR-0005 (app-factory, 422/503 contract, load-test-as-artifact); Docker verification deferred-noted if daemon absent; §8 self-review; full gate; **self-merge to main** |

### Stage 6 — integration  (branch `stage/06-integration`)
| M | slug | deliverable |
|---|---|---|
| 1 | smoke | `scripts/smoke.sh` + `make smoke` (sampled slice → data build → forecast train+register → serve → 3 `/forecast` calls → assert shapes + `model_version`); `tests/e2e/test_smoke.py` `@pytest.mark.e2e` on committed `tests/fixtures/e2e/` sample; CI `smoke` job |
| 2 | docs-merge | README Phase 0–1 sections (arch slice, copy-paste `make` commands + expected output, status); `docs/skills-map.md` first entries; verify `make setup && make smoke` from a fresh worktree; full gate incl. `-m e2e`; **self-merge to main** → *Phase 1 Done* |

## 5. On completion (or hard stop)

Write / update `reports/progress/STAGES-2-6-SUMMARY.md`:
- Per-stage: milestone table, commit shas, merge commit, gate results, §8
  self-review verdict.
- Autonomous decisions log (`Dxx`) with one-line rationale each — flagged for
  optional human reversal.
- Real-artifact results (`reports/backtest/`, `reports/loadtest/`,
  `reports/sim/`) with headline numbers.
- Exact resume point if stopped early.
