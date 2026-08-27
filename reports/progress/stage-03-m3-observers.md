# Stage 3 — M3 observers
**Status:** done · ruff·mypy·pytest 74 passed
- `sim/des/metrics.py`: `SimMetrics` + `summarize(events, *, n_drivers, horizon_min)`
  — requests / rides_completed / cancellations / cancel_rate / mean|median|p90
  wait / driver_idle_pct (busy driver-minutes from match→trip-completed spans,
  vectorised merge).
- `sim/des/observers.py`: `EventObserver` ABC; `EventLogWriter`;
  `MetricsCollector(n_drivers, horizon_min)` whose `result()` == `summarize` on
  the same stream.
- tests: writer captures all events; collector == independent summary; value
  sanity (4 req, 3 completed, 0.25 cancel rate, mean wait matches).
- Next: M4 simulation (SimPy).
