import numpy as np
import pytest

from ridepulse.sim.mdp.interface import (
    MdpSimulator,
    NotImplementedMdpSimulator,
)


def test_protocol_and_stub_import() -> None:
    sim = NotImplementedMdpSimulator()
    assert isinstance(sim, MdpSimulator)  # runtime_checkable Protocol
    assert sim.dt_min == 5.0


def test_stub_methods_raise() -> None:
    sim = NotImplementedMdpSimulator()
    with pytest.raises(NotImplementedError, match="Phase 6"):
        sim.reset(0)
    with pytest.raises(NotImplementedError, match="Phase 6"):
        sim.step(np.zeros(1), np.zeros(1))
