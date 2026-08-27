"""`MdpSimulator` — the time-stepped simulator contract used by RL in Phase 6.

**Stub.** Every method raises :class:`NotImplementedError`. The shape is fixed
now so Stage 3's ``sim.core`` boundary does not need to change when Phase 6
implements this on top of the same :class:`~ridepulse.sim.core.city.CityModel`.

Design intent (ADR-0002):
- fixed timestep ``dt_min``; vectorised NumPy state; low-dimensional observation
- ``State`` = per-zone idle-driver counts, per-zone waiting-rider counts,
  time-of-week features, and the current demand forecast
- ``Action`` = a repositioning assignment for idle drivers
- reward = completed rides in the step (minus a small idle penalty)
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy.typing as npt

State = npt.NDArray[Any]
Action = npt.NDArray[Any]
StepResult = tuple[State, float, bool, dict[str, Any]]


@runtime_checkable
class MdpSimulator(Protocol):
    dt_min: float

    def reset(self, seed: int) -> State:
        """Return the initial observation for a new episode."""
        ...

    def step(self, state: State, action: Action) -> StepResult:
        """Advance one ``dt_min`` step -> (next_state, reward, done, info)."""
        ...


class NotImplementedMdpSimulator:
    """Placeholder concrete class — Phase 6 replaces this."""

    dt_min: float = 5.0

    def reset(self, seed: int) -> State:
        raise NotImplementedError("sim.mdp is implemented in Phase 6 (ADR-0002)")

    def step(self, state: State, action: Action) -> StepResult:
        raise NotImplementedError("sim.mdp is implemented in Phase 6 (ADR-0002)")
