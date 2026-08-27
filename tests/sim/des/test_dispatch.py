from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pandas as pd

from ridepulse.sim.core.city import CityModel
from ridepulse.sim.core.entities import Driver, Rider
from ridepulse.sim.des.dispatch import NearestDriverPolicy, make_policy

NOW = pd.Timestamp("2023-01-04 08:00")


def _city() -> CityModel:
    from ridepulse.sim.core.grid import CityGrid

    return cast(CityModel, SimpleNamespace(grid=CityGrid.load()))


def _rider(rid: int, zone: int, offset_min: int) -> Rider:
    return Rider(rid, origin_zone=zone, dest_zone=1,
                 request_ts=NOW + pd.Timedelta(minutes=offset_min), patience_min=8)


def test_assigns_nearest_within_radius_no_double_booking() -> None:
    city = _city()
    pol = NearestDriverPolicy(radius_km=5.0)
    riders = [_rider(1, 161, 0), _rider(2, 161, 1)]
    drivers = [Driver(10, zone=161), Driver(11, zone=162), Driver(12, zone=100)]

    out = pol.assign(riders, drivers, city, NOW)

    assert len(out) == 2
    assert {a.driver_id for a in out} == {10, 11}          # two closest, no reuse
    assert {a.rider_id for a in out} == {1, 2}
    # rider 1 (FIFO first) gets the co-located driver 10
    assert next(a for a in out if a.rider_id == 1).driver_id == 10


def test_rider_with_no_driver_in_radius_waits() -> None:
    city = _city()
    pol = NearestDriverPolicy(radius_km=0.5)
    riders = [_rider(1, 1, 0)]           # zone 1 = Newark, far from everything
    drivers = [Driver(10, zone=132)]     # JFK

    assert pol.assign(riders, drivers, city, NOW) == []


def test_fewer_drivers_than_riders_serves_fifo() -> None:
    city = _city()
    pol = NearestDriverPolicy(radius_km=50.0)
    riders = [_rider(3, 161, 5), _rider(1, 161, 0), _rider(2, 161, 2)]
    drivers = [Driver(10, zone=161)]

    out = pol.assign(riders, drivers, city, NOW)
    assert len(out) == 1
    assert out[0].rider_id == 1          # earliest request wins the only driver


def test_make_policy_registry() -> None:
    p = make_policy("nearest_driver", radius_km=2.0)
    assert isinstance(p, NearestDriverPolicy)
    assert p.radius_km == 2.0
    try:
        make_policy("bogus")
    except KeyError as e:
        assert "unknown dispatch policy" in str(e)
    else:
        raise AssertionError("expected KeyError")
