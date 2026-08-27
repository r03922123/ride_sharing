# Stage 3 — M2 dispatch
**Status:** done · ruff·mypy·pytest 72 passed
- `sim/des/dispatch.py`: `DispatchPolicy` ABC (`assign(pending, idle, city, now)`);
  `NearestDriverPolicy(radius_km)` — FIFO over waiting riders, each takes the
  closest idle driver within radius, no double-booking, unreachable riders wait;
  `POLICIES` registry + `make_policy(name, **params)`.
- tests: nearest assigned / no reuse / FIFO first pick; out-of-radius waits;
  fewer drivers than riders → earliest request served; registry + unknown raises.
- Next: M3 observers.
