# Stage 3 — M1 events
**Status:** done · ruff·mypy·pytest 68 passed
- `sim/des/events.py`: `Event` base + `RiderRequested/RiderMatched/RiderCancelled/
  PickupCompleted/TripCompleted/DriverRepositioned` (frozen dataclasses);
  `EventLog.append/to_frame/to_parquet/from_parquet`. `to_frame` pins dtypes
  (`string`/datetime/`Int64`/`Float64`) so parquet round-trips exactly.
- tests: kind == class name; frame sorted + all 7 columns; parquet round-trip.
- Next: M2 dispatch.
