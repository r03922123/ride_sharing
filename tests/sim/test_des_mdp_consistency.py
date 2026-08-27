"""des <-> mdp aggregate consistency (activated in Phase 6 — see ADR-0002).

Written now so the contract is committed alongside the split. `sim.mdp` is a
stub until Phase 6, so this is skipped.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ridepulse.sim.core.city import CityModel
from ridepulse.sim.des.dispatch import NearestDriverPolicy
from ridepulse.sim.des.metrics import summarize
from ridepulse.sim.des.simulation import SimConfig, Simulation

TOLERANCE = 0.15  # aggregate demand-served and mean-wait agreement


@pytest.mark.skip(reason="sim.mdp is implemented in Phase 6 (ADR-0002)")
def test_des_and_mdp_agree_on_aggregates(small_city: CityModel) -> None:
    start = pd.Timestamp("2023-01-04 07:00")
    cfg = SimConfig(
        city=small_city,
        policy=NearestDriverPolicy(radius_km=8.0),
        start=start,
        hours=6.0,
        seed=3,
    )
    des_df = Simulation(cfg).run().to_frame()
    des = summarize(des_df, n_drivers=len(small_city.drivers), horizon_min=6 * 60)

    # --- Phase 6 fills this in ---
    from ridepulse.sim.mdp.interface import NotImplementedMdpSimulator  # noqa: F401

    mdp_rides_completed = des.rides_completed  # placeholder
    mdp_mean_wait = des.mean_wait_min          # placeholder

    assert abs(mdp_rides_completed - des.rides_completed) <= TOLERANCE * max(
        des.rides_completed, 1
    )
    assert abs(mdp_mean_wait - des.mean_wait_min) <= TOLERANCE * max(
        des.mean_wait_min, 1e-6
    )
