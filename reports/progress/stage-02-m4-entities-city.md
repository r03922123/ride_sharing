# Stage 2 — M4 entities-city

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (18 files) · pytest 65 passed

## Done
- `src/ridepulse/sim/core/entities.py`:
  - `RiderState` / `DriverState` (`StrEnum`); `IllegalTransition`.
  - `Rider` (origin/dest zone, request_ts, patience_min, state) and `Driver`
    (zone, state) with `set_state` enforcing `_RIDER_LEGAL` / `_DRIVER_LEGAL`
    transition tables; `Rider.is_terminal`.
  - `Assignment` (frozen, value-equal; `_meta` excluded from equality).
- `src/ridepulse/sim/core/city.py`:
  - `CityConfig` (n_drivers, seed, demand_profile_path, driver_placement).
  - `CityModel.build(config)` — loads grid + zones + demand artifact, places the
    fleet `uniform` or `demand_weighted` (via `DemandProfile.total_weekly_pickups`)
    with a seeded RNG. Exposes `.grid`, `.zones`, `.demand`, `.drivers`.
- `configs/sim/baseline.yaml` — city / run / dispatch blocks (consumed in Stage 3).
- Tests: rider happy path + every illegal transition raises; driver cycle;
  `CityModel.build` deterministic per seed; exposes the three components;
  demand-weighted placement puts >80 % of drivers in the busy zone, uniform
  spreads across >100 zones.

## Decisions / deviations from plan
- **D12**: added `DriverState.REPOSITIONING` and `total_weekly_pickups()` now
  (both needed for Phase 6 RL) — pure additions, no behaviour change.

## Blocked / deferred
- none.

## Next
- M5 adr-merge — ADR-0002 (core/des/mdp split) + `docs/lld/sim-class-diagram.md`;
  §8 self-review; **self-merge Stage 2 to main**.
