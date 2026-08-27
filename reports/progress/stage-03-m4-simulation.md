# Stage 3 — M4 simulation
**Status:** done · ruff·mypy·pytest 77 passed
- `sim/des/simulation.py`: `SimConfig` (city, policy, start, hours, patience,
  speed, dispatch interval, seed, observers) + `Simulation`:
  - per-active-zone Poisson arrival process (piecewise rate from `DemandProfile`,
    exponential inter-arrivals from one seeded RNG);
  - per-rider patience timer → `RiderCancelled` if still waiting;
  - dispatch loop every `dispatch_interval_min` → `policy.assign` → `_serve`;
  - `_serve`: match → travel to pickup → `PickupCompleted` → travel to dest →
    `TripCompleted`; driver zone + state updated each leg.
  - time unit = minutes since `start`; `run()` returns the `EventLog`.
- tests (fixture `small_city` = calibrated 4-zone demand, 60 drivers):
  events produced incl. `TripCompleted`; **same seed → byte-identical frame**;
  different seed differs.
- Next: M5 invariants + mdp stub + consistency test (skipped) + CLI.
