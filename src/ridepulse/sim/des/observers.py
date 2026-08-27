"""Observers on the simulation event stream (the Observer pattern).

Each observer subscribes independently; `Simulation` fans every event out to all
of them. `MetricsCollector` accumulates the same quantities `metrics.summarize`
derives from the raw log, so the two must agree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ridepulse.sim.des.events import Event, EventLog
from ridepulse.sim.des.metrics import SimMetrics, summarize


class EventObserver(ABC):
    @abstractmethod
    def on_event(self, event: Event) -> None: ...


class EventLogWriter(EventObserver):
    def __init__(self, log: EventLog | None = None) -> None:
        self.log = log if log is not None else EventLog()

    def on_event(self, event: Event) -> None:
        self.log.append(event)


class MetricsCollector(EventObserver):
    """Streaming tally; `result()` matches `summarize` on the same run."""

    def __init__(self, *, n_drivers: int, horizon_min: float) -> None:
        self._n_drivers = n_drivers
        self._horizon_min = horizon_min
        self._log = EventLog()

    def on_event(self, event: Event) -> None:
        self._log.append(event)

    def result(self) -> SimMetrics:
        return summarize(
            self._log.to_frame(),
            n_drivers=self._n_drivers,
            horizon_min=self._horizon_min,
        )
