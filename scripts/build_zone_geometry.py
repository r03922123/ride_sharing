"""Derive committed zone-geometry assets from the TLC taxi-zones shapefile.

Outputs (checked in, ~0.6 MB total):
  src/ridepulse/sim/core/data/zone_centroids.parquet   zone_id, lat, lon
  src/ridepulse/sim/core/data/zone_distances.npy       263x263 great-circle km

Run once (needs the `geo` extra):
  uv run --extra geo python scripts/build_zone_geometry.py
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

SHAPEFILE_ZIP = Path("data/raw/taxi_zones_shapefile.zip")
OUT_DIR = Path("src/ridepulse/sim/core/data")
EARTH_KM = 6371.0088


def _haversine_km(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Pairwise great-circle distances (km) for centroid arrays -> (n, n)."""
    la = np.radians(lat)[:, None]
    lo = np.radians(lon)[:, None]
    dphi = la - la.T
    dlmb = lo - lo.T
    a = np.sin(dphi / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(SHAPEFILE_ZIP).extractall(tmp)
        gdf = gpd.read_file(next(Path(tmp).rglob("*.shp")))

    gdf = (
        gdf[gdf["LocationID"].between(1, 263)]
        .sort_values("LocationID")
        .reset_index(drop=True)
    )
    assert list(gdf["LocationID"]) == list(range(1, 264)), "expected zones 1..263"

    centroids = gdf.to_crs(2263).geometry.centroid.to_crs(4326)
    lat = centroids.y.to_numpy()
    lon = centroids.x.to_numpy()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {"zone_id": gdf["LocationID"].to_numpy(), "lat": lat, "lon": lon}
    ).to_parquet(OUT_DIR / "zone_centroids.parquet", index=False)

    dist = _haversine_km(lat, lon).astype("float64")
    np.save(OUT_DIR / "zone_distances.npy", dist)

    print(f"wrote {OUT_DIR/'zone_centroids.parquet'} (263 rows)")
    print(f"wrote {OUT_DIR/'zone_distances.npy'} {dist.shape} "
          f"max {dist.max():.1f} km")


if __name__ == "__main__":
    main()
