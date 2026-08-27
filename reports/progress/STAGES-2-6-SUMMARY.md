# Autonomous block — Stages 2–6 — SUMMARY

**Stopped at:** end of **Stage 3** → spec §14 **Phase 0 Done** (an acceptable
stop point per the roadmap; token-limit aware). Stages 4–6 not started.
**`main`** @ `fc41699` — releasable. **86 tests pass, 1 skipped** (the Phase-6
consistency test). `ruff` + `mypy --strict` clean.

## Stages completed

| Stage | Package | Milestones | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| 2 | `sim.core` | M1 zone-geometry · M2 zones · M3 demand · M4 entities-city · M5 adr-merge | `8e9e143` | ruff·mypy·65 tests |
| 3 | `sim.des` (+ `sim.mdp` stub) | M1 events · M2 dispatch · M3 observers · M4 simulation · M5 invariants-stub · M6 adr-merge | `fc41699` | ruff·mypy·86 tests, 1 skipped |

Per-milestone detail: `reports/progress/stage-02-m*.md`, `stage-03-m*.md`.

## What exists now (`src/ridepulse/sim/`)

```
core/
  grid.py        CityGrid — zone-centroid distances, travel_time_min
  zones.py       ZoneMap — id <-> name <-> borough
  demand.py      DemandProfile — (zone x hour-of-week) Poisson calibrate/save/
                 arrival_rate/sample_arrivals/total_weekly_pickups
  entities.py    Rider/Driver StrEnum state machines, IllegalTransition, Assignment
  city.py        CityConfig + CityModel.build (seeded fleet placement)
  data/          committed: zone_centroids.parquet, zone_distances.npy, zone_lookup.csv
des/
  events.py      Event dataclasses + EventLog (parquet, (ts,seq) total order)
  dispatch.py    DispatchPolicy ABC + NearestDriverPolicy + POLICIES + make_policy
  observers.py   EventObserver ABC + EventLogWriter + MetricsCollector
  metrics.py     summarize(events) -> SimMetrics (pure)
  simulation.py  SimConfig + Simulation (SimPy; arrivals/patience/dispatch/serve)
  runner.py      run_scenario(yaml, out) -> event_log.parquet + metrics.json
mdp/
  interface.py   MdpSimulator Protocol + NotImplementedMdpSimulator (Phase 6 stub)
```
CLI added: `ridepulse sim calibrate`, `ridepulse sim run`. `make sim` wired.
ADRs 0002 (core/des/mdp split), 0003 (dispatch Strategy / event Observer).
`docs/lld/sim-class-diagram.md`.

## Real-artifact results

- `ridepulse sim calibrate` on real `cleaned_trips` (2 months): 0.1 s.
- `make sim` — 24 h Wednesday, 2,500 drivers, `nearest_driver` r=3 km:
  - requests **102,111** · completed **98,110** · cancel_rate **0.0299**
  - mean wait **2.72 min** · median **0.99** · p90 **7.43 min**
  - driver idle **60.9 %**
  All in plausible ranges for a demand-weighted fleet.

## Autonomous decisions (reverse if you disagree)

| # | Decision | Why |
| --- | --- | --- |
| D11 | Shapefile read via extract-to-tempdir | pyogrio `/vsizip/` refused the archive; script-only |
| D12 | `DriverState.REPOSITIONING` + `total_weekly_pickups()` added early | needed by Phase 6; pure additions |
| D13 | `seq` column + `(ts, seq)` event sort | invariant tests found non-deterministic tie order; needed for a total causal order |
| D14 | `SimConfig` bundles city + policy + params | plan named the fields, not the container |
| D15 | Trip destination sampled demand-weighted | plan left destinations unspecified |
| — | Stage-1 open questions resolved per roadmap §0 (EtaSchema keeps `pickup_ts`/`split`; cleaning thresholds fixed; local no-ff self-merge replaces PRs) | |

## Resume point — Stage 4 (`forecast`)

Branch `stage/04-forecast` off `main` @ `fc41699`. Plan Stage 4 milestones:
dataset → backtest+`LeakageError` → split-conformal intervals → LightGBM model +
seasonal-naive baseline → MLflow registry + backtest report → ADR-0004 + run
`make backtest` on real data + self-merge. Then Stage 5 (`serving`), Stage 6
(integration → Phase 1 Done). Roadmap: `docs/progress/ROADMAP-autonomous-stages-2-6.md`.
