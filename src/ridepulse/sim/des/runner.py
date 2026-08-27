"""Load a scenario YAML, run the discrete-event sim, write artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from ridepulse.sim.core.city import CityConfig, CityModel
from ridepulse.sim.des.dispatch import make_policy
from ridepulse.sim.des.metrics import summarize
from ridepulse.sim.des.simulation import SimConfig, Simulation


def run_scenario(config_path: str | Path, out_dir: str | Path) -> dict[str, float]:
    cfg: dict[str, Any] = yaml.safe_load(Path(config_path).read_text())
    city_cfg, run_cfg, disp_cfg = cfg["city"], cfg["run"], cfg["dispatch"]

    city = CityModel.build(CityConfig(**city_cfg))
    policy = make_policy(disp_cfg["policy"], **disp_cfg.get("params", {}))
    sim_cfg = SimConfig(
        city=city,
        policy=policy,
        start=pd.Timestamp(run_cfg["start"]),
        hours=float(run_cfg["hours"]),
        patience_min=float(run_cfg["rider_patience_min"]),
        speed_kmh=float(run_cfg["trip_speed_kmh"]),
        seed=int(city_cfg["seed"]),
    )

    log = Simulation(sim_cfg).run()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log.to_parquet(out_dir / "event_log.parquet")

    metrics = summarize(
        log.to_frame(),
        n_drivers=int(city_cfg["n_drivers"]),
        horizon_min=float(run_cfg["hours"]) * 60.0,
    ).to_dict()
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics
