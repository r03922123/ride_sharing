# ADR-0003: `sim.des` — dispatch as Strategy, event stream as Observer

**Status:** accepted
**Date:** 2026-08-28
**Context:** Plan Stage 3; spec §8 (LLD), §14 Phase 0. Builds on ADR-0002.

## Decisions

### SimPy for the engine

The `des` loop is genuinely event-driven: riders arrive on a Poisson process,
cancel exactly at their patience horizon, and drivers free up mid-tick. SimPy's
process/timeout model expresses this directly (`yield env.timeout(...)`) without
a hand-rolled event heap. Time unit is **minutes since `config.start`**; wall
timestamps are derived only when an event is emitted.

Rejected: a fixed-timestep loop (that is `sim.mdp`'s job, ADR-0002) — it would
blur cancellation timing and force a sub-step ordering convention here.

### `DispatchPolicy` — Strategy + ABC

Matching is the one part expected to grow (batched assignment, radius-then-queue
variants, and in Phase 6 a learned repositioning policy). It lives behind
`DispatchPolicy.assign(pending, idle, city, now) -> list[Assignment]` with a
`POLICIES` name→class registry and `make_policy(name, **params)`. The engine
never imports a concrete policy; scenarios name one in YAML.

`NearestDriverPolicy` (the baseline, D5): waiting riders in FIFO request order,
each takes the closest idle driver within `radius_km`, no double-booking,
unreachable riders wait for the next tick.

### Event stream — Observer

`Simulation` fans every `Event` to a list of `EventObserver`s. Today:
`EventLogWriter` (builds the canonical `EventLog`) and `MetricsCollector`
(streaming tally whose `result()` equals `metrics.summarize` on the same log).
Monitoring and, later, an RL trajectory recorder subscribe the same way — the
engine does not change.

### Total event order

Events carry a monotonic `seq` (emission index). The canonical frame is sorted
by `(ts, seq)`, giving a deterministic total causal order even when several
events share a timestamp (zero-distance pickups, same-tick free-and-rematch).
The conservation-invariant tests depend on this.

## Consequences

- A run is fully reproducible: one seeded RNG + deterministic SimPy scheduling +
  `(ts, seq)` ordering → byte-identical `event_log.parquet` for a given config.
- `summarize` is a pure function of the log; metrics can always be recomputed
  from the artifact.
- The `des`/`mdp` consistency test (ADR-0002) is committed and skipped until
  Phase 6.
