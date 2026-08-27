import numpy as np
import pytest

from ridepulse.sim.core.grid import CityGrid


def test_load_has_263_zones() -> None:
    grid = CityGrid.load()
    assert grid.zone_ids == list(range(1, 264))


def test_distance_matrix_properties() -> None:
    grid = CityGrid.load()
    d = np.array([[grid.distance_km(a, b) for b in grid.zone_ids[:20]]
                  for a in grid.zone_ids[:20]])
    assert np.allclose(d, d.T)                      # symmetric
    assert np.allclose(np.diag(d), 0.0)            # zero on the diagonal
    assert np.isfinite(d).all()
    assert (d >= 0).all()


def test_travel_time_monotonic_in_distance() -> None:
    grid = CityGrid.load()
    near = grid.distance_km(1, 2)
    far = grid.distance_km(1, 132)  # zone 132 = JFK, far from Newark (zone 1)
    assert far > near
    assert grid.travel_time_min(1, 132, 30.0) > grid.travel_time_min(1, 2, 30.0)
    assert grid.travel_time_min(5, 5, 30.0) == 0.0


def test_travel_time_scales_with_speed() -> None:
    grid = CityGrid.load()
    t30 = grid.travel_time_min(1, 132, 30.0)
    t60 = grid.travel_time_min(1, 132, 60.0)
    assert t30 == pytest.approx(2 * t60)


def test_invalid_inputs_raise() -> None:
    grid = CityGrid.load()
    with pytest.raises(KeyError):
        grid.distance_km(1, 999)
    with pytest.raises(ValueError, match="positive"):
        grid.travel_time_min(1, 2, 0.0)


def test_bad_matrix_shape_raises() -> None:
    with pytest.raises(ValueError, match="shape"):
        CityGrid([1, 2, 3], np.zeros((2, 2)))
