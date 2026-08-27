# Stage 2 — M5 adr-merge

**Commit:** (this commit)
**Status:** done — Stage 2 complete
**Gate:** ruff pass · mypy pass (18 files) · pytest 65 passed

## Done
- `docs/adr/0002-sim-core-des-mdp-split.md` — the spec §8 headline ADR: why two
  simulators (opposite hot paths: event fidelity vs step throughput), what each
  optimises, how they stay consistent (shared `CityModel` + skipped consistency
  test written in Stage 3, active in Phase 6), the layered-core + Template-Method
  / State / Strategy / Observer model, and the two rejected alternatives
  (one-simulator-two-modes; two independent codebases).
- `docs/lld/sim-class-diagram.md` — mermaid class diagram of `sim.core` (grid,
  zones, demand, entities, city), with Stage-3 `des` classes shown dashed.

## §8 self-review
- *Can a consumer use each `sim.core` unit without reading its internals?* Yes —
  `CityGrid` / `ZoneMap` / `DemandProfile` / `CityModel` each have a small
  documented surface; call sites in tests never reach past it.
- *Can internals change without breaking consumers?* Yes — distance backend,
  calibration granularity, and fleet-placement maths are all private; the public
  signatures (`distance_km`, `arrival_rate`, `build`) are stable and are what
  `des` will depend on.
- No unit does two jobs; `demand`'s calibration vs. query split is explicit.

## Merge
`git merge --no-ff stage/02-sim-core -> main`, pushed. `main` releasable:
`ridepulse sim calibrate` works end-to-end; 65 tests green.

## Autonomous decisions this stage
- D11 shapefile via extract-to-tempdir (pyogrio `/vsizip/` refused the archive).
- D12 added `DriverState.REPOSITIONING` + `DemandProfile.total_weekly_pickups`
  early (needed by Phase 6; pure additions).
- Distance unit = km throughout.

## Next
- Stage 3 `sim.des` on `stage/03-sim-des`.
