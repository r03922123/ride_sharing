import pytest

from ridepulse.sim.core.zones import ZoneMap


def test_loads_263_zones() -> None:
    zm = ZoneMap.load()
    assert len(zm) == 263
    assert zm.zone_ids == list(range(1, 264))


def test_id_name_borough_round_trip() -> None:
    zm = ZoneMap.load()
    assert zm.name(1) == "Newark Airport"
    assert zm.borough(1) == "EWR"
    assert zm.id_by_name("Newark Airport") == 1
    # a Manhattan zone
    assert zm.borough(zm.id_by_name("Midtown Center")) == "Manhattan"


def test_unknown_id_raises() -> None:
    zm = ZoneMap.load()
    with pytest.raises(KeyError):
        zm.name(0)
    with pytest.raises(KeyError):
        zm.borough(264)


def test_unknown_name_raises() -> None:
    zm = ZoneMap.load()
    with pytest.raises(KeyError):
        zm.id_by_name("Nowhere")
