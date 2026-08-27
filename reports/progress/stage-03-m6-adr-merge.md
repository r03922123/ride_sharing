# Stage 3 — M6 adr-merge  (Stage 3 complete → spec Phase 0 Done)
**Status:** done · ruff·mypy·pytest 86 passed, 1 skipped
- `docs/adr/0003-des-dispatch-and-events.md` — SimPy choice; `DispatchPolicy`
  Strategy + registry; event stream Observer; `(ts, seq)` total causal order.
- `docs/lld/sim-class-diagram.md` extended with `Simulation`, `SimConfig`,
  `DispatchPolicy`/`NearestDriverPolicy`, `EventObserver`/`EventLogWriter`/
  `MetricsCollector`, `EventLog`/`Event`, and the `MdpSimulator` stub.

## §8 self-review
- *Consumer can use without internals?* Yes — `Simulation(cfg).run()` returns an
  `EventLog`; `summarize` is pure over its frame; `make_policy` hides policy
  classes. Callers touch only `SimConfig`, `run`, `to_frame`, `summarize`.
- *Internals swappable?* Yes — dispatch behind the ABC + registry; observers
  behind the ABC; the SimPy engine could be replaced without changing the event
  schema or metrics. `sim.core` was not modified by `des` (ADR-0002 held).
- No unit does two jobs; calibration/query, engine/metrics, policy/engine are
  each separated.

## Merge
`git merge --no-ff stage/03-sim-des -> main`, pushed. **Spec §14 Phase 0 Done:**
`make data` reproduces the feature tables; `sim.des` runs a scenario and emits an
event log; conservation invariants green in CI-equivalent gate.

## Autonomous decisions this stage
- D13 added `seq` to the event schema + `(ts, seq)` sort — required for a
  deterministic total order (invariant tests found the bug).
- D14 `SimConfig` bundles city+policy+params (plan named the fields, not the
  container).
- D15 destination zone sampled demand-weighted (plan left trip destinations
  unspecified).

## Next
- Stage 4 `forecast` on `stage/04-forecast`.
