# Stage 2 — M1 zone-geometry

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (14 files) · pytest 46 passed

## Done
- `scripts/build_zone_geometry.py` — extracts the TLC zones shapefile, computes
  centroids (project to EPSG:2263, centroid, back to WGS84), writes the committed
  assets. Vectorised haversine for the full pairwise matrix.
- Committed assets (`.gitignore` exception added for `src/ridepulse/sim/core/data/`):
  - `zone_centroids.parquet` — `zone_id, lat, lon` for zones 1..263 (8 KB)
  - `zone_distances.npy` — 263×263 float64 great-circle km (541 KB), max 52.4 km
- `src/ridepulse/sim/core/grid.py` — `CityGrid.load()`, `.zone_ids`,
  `.distance_km(a,b)`, `.travel_time_min(a,b,speed_kmh)` (straight-line at
  constant speed; routing is out of scope).
- `tests/sim/core/test_grid.py` — 263 zones load; distance matrix symmetric,
  zero-diagonal, finite, non-negative; travel time monotonic in distance,
  `t(a,a)=0`, scales inversely with speed; unknown zone → `KeyError`,
  non-positive speed → `ValueError`; bad matrix shape → `ValueError`.

## Decisions / deviations from plan
- **D11**: shapefile read via extract-to-tempdir (pyogrio's `/vsizip/` refused
  the archive). Script-only, one-time; no runtime impact.
- Distance unit is km throughout (plan said "distance matrix"; km chosen for
  readable travel-time math).

## Blocked / deferred
- none.

## Next
- M2 zones — `sim/core/zones.py` (`ZoneMap.load`) + id↔name↔borough round-trip.
