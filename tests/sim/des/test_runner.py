from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from ridepulse.sim.core.demand import DemandProfile
from ridepulse.sim.des.runner import run_scenario


def test_run_scenario_writes_artifacts(tmp_path: Path) -> None:
    # tiny calibrated profile
    rows = []
    start = pd.Timestamp("2023-01-02 00:00")
    for h in range(2 * 168):
        ts = start + pd.Timedelta(hours=h)
        for z, n in ((161, 10), (162, 6)):
            for _ in range(n):
                rows.append(
                    {
                        "pickup_ts": ts + pd.Timedelta(minutes=1),
                        "dropoff_ts": ts + pd.Timedelta(minutes=11),
                        "pu_location_id": z,
                        "do_location_id": z,
                        "trip_distance": 1.0,
                        "passenger_count": 1,
                        "duration_min": 10.0,
                    }
                )
    cleaned = tmp_path / "cleaned.parquet"
    pd.DataFrame(rows).to_parquet(cleaned)
    profile = DemandProfile.calibrate(cleaned).save(tmp_path / "profile.parquet")

    config = tmp_path / "scenario.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "city": {
                    "n_drivers": 40,
                    "seed": 5,
                    "demand_profile_path": str(profile),
                    "driver_placement": "demand_weighted",
                },
                "run": {
                    "start": "2023-01-04 07:00",
                    "hours": 1,
                    "rider_patience_min": 8.0,
                    "trip_speed_kmh": 24.0,
                },
                "dispatch": {"policy": "nearest_driver", "params": {"radius_km": 8.0}},
            }
        )
    )

    out = tmp_path / "out"
    metrics = run_scenario(config, out)

    assert (out / "event_log.parquet").exists()
    assert (out / "metrics.json").exists()
    saved = json.loads((out / "metrics.json").read_text())
    assert saved == metrics
    assert metrics["requests"] > 0
    assert 0.0 <= metrics["driver_idle_pct"] <= 1.0
