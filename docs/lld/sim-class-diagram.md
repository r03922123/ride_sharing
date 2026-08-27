# `ridepulse.sim` — class diagram

`sim.core` (Stage 2) + `sim.des` (Stage 3). `sim.mdp` is an interface stub until
Phase 6. See ADR-0002 (the split) and ADR-0003 (dispatch Strategy, event
Observer).

```mermaid
classDiagram
    class CityGrid {
      +zone_ids: list~int~
      +load() CityGrid
      +distance_km(a, b) float
      +travel_time_min(a, b, speed_kmh) float
    }
    class ZoneMap {
      +load(lookup_csv) ZoneMap
      +name(zone_id) str
      +borough(zone_id) str
      +id_by_name(name) int
    }
    class DemandProfile {
      +calibrate(cleaned_trips_path) DemandProfile
      +from_artifact(path) DemandProfile
      +save(path) Path
      +arrival_rate(zone_id, when) float
      +sample_arrivals(zone_id, t0, t1, rng) list~Timestamp~
      +total_weekly_pickups(zone_id) float
    }
    class Rider {
      +rider_id: int
      +origin_zone: int
      +dest_zone: int
      +patience_min: float
      +state: RiderState
      +set_state(new)
      +is_terminal: bool
    }
    class Driver {
      +driver_id: int
      +zone: int
      +state: DriverState
      +set_state(new)
    }
    class Assignment {
      +rider_id: int
      +driver_id: int
      +ts: Timestamp
    }
    class CityConfig {
      +n_drivers: int
      +seed: int
      +demand_profile_path
      +driver_placement
    }
    class CityModel {
      +grid: CityGrid
      +zones: ZoneMap
      +demand: DemandProfile
      +drivers: list~Driver~
      +build(config) CityModel
    }
    class RiderState {
      <<enumeration>>
      WAITING
      MATCHED
      PICKED_UP
      DROPPED_OFF
      CANCELLED
    }
    class DriverState {
      <<enumeration>>
      IDLE
      TO_PICKUP
      ON_TRIP
      REPOSITIONING
    }

    CityModel --> CityGrid
    CityModel --> ZoneMap
    CityModel --> DemandProfile
    CityModel "1" --> "*" Driver
    CityModel ..> CityConfig : build(config)
    Rider --> RiderState
    Driver --> DriverState

    class SimConfig {
      +city: CityModel
      +policy: DispatchPolicy
      +start; hours; patience_min; speed_kmh; seed
      +observers: list~EventObserver~
    }
    class Simulation {
      +run() EventLog
    }
    class DispatchPolicy {
      <<abstract>>
      +assign(pending, idle, city, now) list~Assignment~
    }
    class NearestDriverPolicy {
      +radius_km: float
    }
    class EventObserver {
      <<abstract>>
      +on_event(event)
    }
    class EventLogWriter
    class MetricsCollector {
      +result() SimMetrics
    }
    class EventLog {
      +append(event)
      +to_frame() DataFrame
      +to_parquet(path)
    }
    class Event {
      <<abstract>>
      +ts: Timestamp
      +kind: str
    }
    class MdpSimulator {
      <<Protocol, Phase 6 stub>>
      +reset(seed) State
      +step(state, action) StepResult
    }

    Simulation ..> SimConfig
    Simulation --> EventLog
    Simulation ..> DispatchPolicy
    Simulation ..> EventObserver
    DispatchPolicy <|-- NearestDriverPolicy
    DispatchPolicy ..> Assignment
    EventObserver <|-- EventLogWriter
    EventObserver <|-- MetricsCollector
    EventLogWriter --> EventLog
    EventLog "1" --> "*" Event
    MdpSimulator ..> CityModel : (Phase 6)
```
