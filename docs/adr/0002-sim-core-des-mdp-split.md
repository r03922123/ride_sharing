# ADR-0002: One city model, two simulators (`core` / `des` / `mdp`)

**Status:** accepted
**Date:** 2026-08-28
**Context:** Plan Stage 2–3; spec §3 (architecture), §8 (LLD), §14 Phase 0,
§7c / Phase 6 (RL + off-policy evaluation).

## Decision

`ridepulse.sim` is split into three layers:

| Layer | Role | Optimised for |
| --- | --- | --- |
| `sim.core` | The **shared, deterministic city model**: `CityGrid` (zone-centroid distances, travel time), `ZoneMap`, `DemandProfile` ((zone × hour-of-week) Poisson), `Rider` / `Driver` state machines, `CityModel.build`. No simulation loop. | being the single source of geography + demand + entity rules |
| `sim.des` | **Discrete-event** simulator on `sim.core` (SimPy). Event-accurate ordering, arbitrary inter-event distributions, per-rider metrics, pluggable `DispatchPolicy`. | the agent's what-if calls and the Phase 4a A/B study — realism per rider |
| `sim.mdp` | **Time-stepped** simulator on `sim.core` (fixed Δt, vectorised NumPy, low-dimensional state). Interface stub in Phase 0; implemented in Phase 6. | RL: 10⁵–10⁷ environment steps at CPU speed |

### Why two simulators rather than one

The two use-cases have opposite hot paths. The A/B study needs *event fidelity*
(a rider cancels at exactly their patience horizon; a driver becomes idle the
instant a trip ends) and runs for a few hundred simulated days. RL needs *step
throughput* — a discrete-event engine with a Python event heap cannot deliver
10⁶+ steps in minutes, and RL does not need sub-step event ordering. Forcing both
through one engine would either cripple RL or complicate the A/B engine with a
"fast mode" that quietly changes semantics.

### How they stay consistent

- Both are constructed from the same `CityModel` — identical grid, zone map,
  demand profile, and initial fleet for a given `CityConfig` + seed.
- `tests/sim/test_des_mdp_consistency.py` asserts that, on an identical scenario
  and seed, `des` and `mdp` agree on aggregate demand served and mean wait time
  within a documented tolerance. It is **written in Stage 3 and skipped**
  (`sim.mdp` is a stub until Phase 6); Phase 6 removes the skip. Divergence
  beyond tolerance is then a test failure, not a judgement call.

### Class model & patterns

- **Layered core + Template Method:** `sim.core` holds the invariant domain
  logic; `des` and `mdp` are thin engines that call into it. Neither engine
  re-implements distance, demand, or transition rules.
- **State pattern (lightweight):** `Rider` / `Driver` carry an explicit `state`
  and a transition table (`_RIDER_LEGAL` / `_DRIVER_LEGAL`); illegal moves raise
  `IllegalTransition`, which the Stage 3 conservation invariants depend on.
- **Strategy (Stage 3):** `DispatchPolicy` ABC — matching logic is swappable
  without touching the engine.
- **Observer (Stage 3):** the `des` event stream feeds an `EventLog`, a
  `MetricsCollector`, and (later) monitoring, each subscribing independently.

## Alternatives considered

1. **One simulator, two modes** — a single engine with an event-driven and a
   time-stepped mode. Rejected: the mode flag leaks into every code path and the
   two modes drift in semantics; "it's the same simulator" stops being true.
2. **Two fully independent codebases** — no shared `sim.core`. Rejected: demand
   calibration, the distance model, and entity rules would be duplicated and
   would diverge; the consistency test would be comparing two different cities.

## Consequences

- A small up-front cost: `sim.core` must expose everything both engines need
  before either is built (done in Stage 2).
- The consistency test is the contract; it must stay green once Phase 6 lands.
- `sim.mdp`'s state abstraction (zone/time granularity) is deliberately deferred
  to Phase 6 start (spec §16).
