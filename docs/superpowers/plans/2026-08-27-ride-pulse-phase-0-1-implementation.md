# ride-pulse — Phase 0 + Phase 1 Implementation Plan

**Date:** 2026-08-27
**Status:** Ready to execute
**Author:** csam020410@gmail.com
**Scope:** Spec §14 Phase 0 (Data & simulation foundation) + Phase 1 (Forecasting
service) only. Everything from Phase 2 on is out of scope for this plan.
**Source spec:** [`docs/superpowers/specs/2026-08-27-ride-sharing-ml-portfolio-design.md`](../specs/2026-08-27-ride-sharing-ml-portfolio-design.md)

---

## Planning decisions (locked before execution)

| # | Decision | Value | Rationale |
| --- | --- | --- | --- |
| D1 | Data scope for this plan | **Yellow taxi only, 2023-01..2023-02** (2 months), built in the Codespace | Fast feedback on 2-core / 8 GB. Green + FHV and the full 6-month build (spec §5) become a documented later increment run on the M1 / Oracle box. |
| D2 | Weather feature | **Deferred.** Phase 1 model = calendar + lags + rolling means only | Spec marks NOAA GHCN "stretch". Added later as an explicit `precip × hour` increment with a before/after backtest — mirrors the §1 reference-scenario beat. |
| D3 | PR granularity | **One stacked PR per package**: `scaffold → data → sim.core → sim.des(+mdp stub) → forecast → serving → integration` | Matches spec §8 "design-review gate on every package PR". Each PR merges to `main` with its own green CI + ADR. |
| D4 | Package / env conventions | `src/ridepulse/` import package (repo dir is `ride_sharing`); `uv` + `pyproject.toml`; ruff + mypy + pytest + pre-commit from Phase 0; CI from Phase 0, E2E smoke job added in Phase 1 | Confirmed with author. |
| D5 | Baseline `DispatchPolicy` | **Nearest idle driver within radius `R`, else FIFO queue** | Simplest credible heuristic; other policies (batched, radius-then-queue variants) are later `Strategy` implementations. |
| D6 | CLI framework | **`typer`** (single `ridepulse` console script, subcommand groups `data` / `sim` / `forecast` / `serve`) | Clean declarative CLI; reads well in a portfolio repo. Not pinned by the spec. |
| D7 | Zone spatial model | **Zone-centroid distance matrix**, precomputed once from the TLC zone shapefile and **committed as a data asset**; `geopandas`/`shapely` live in an optional `geo` extra, not a runtime dep | Keeps `sim.core` runtime lean; derived asset is reproducible via a checked-in script. |
| D8 | Demand calibration granularity | Poisson **rate per (zone × hour-of-week)**, estimated from cleaned trips | Coarse, fast, tabular-friendly. Granularity is a documented tunable. |
| D9 | Backtest fold scheme | **Expanding window, weekly test folds** (train ≥ 3 weeks, roll weekly) | 2 months of data is too thin for monthly folds (spec Appendix A.2 assumes 6). Revisit when the full-data increment lands. |
| D10 | Prediction intervals | **Split-conformal** on a held-out calibration slice for the reported interval; native LightGBM quantile models fit and reported alongside for comparison | Calibrated coverage with a simple, defensible method; good talking point. |

**Open items intentionally left for later** (not blockers for Phase 0–1):
Phase 4a intervention choice (spec §16); risk-label source (§16); HF Space envelope
(§16); `sim.mdp` state resolution (§16, resolved at Phase 6 start).

---

## What we are NOT doing in this plan

- No `eta`, `risk`, `agent`, `eval`, `monitoring` packages.
- No `sim.mdp` **implementation** — interface stub + skipped consistency test only
  (spec §14 Phase 0: "interface stub only").
- No RL, no dispatch-matching RL.
- No weather ingestion (D2). No green / FHV / months beyond 2023-02 (D1).
- No MLflow tracking server — local file backend (`mlruns/`) only.
- No Kubernetes, no HF Space deploy, no Gradio, no blog posts, no MkDocs site.
- Load test is a **recorded artifact**, not a CI gate (spec §10: "a breach is a
  documented finding, not a hidden failure").

---

## How to execute

1. Branch per stage off the previous stage's merge (`git switch -c stage/NN-<name>`).
2. Work tasks top-to-bottom. Each task names its **test first**, then the code to
   make it pass. Keep commits small.
3. A stage is **mergeable** only when its "Automated verification" all passes in
   CI and its "Design artifacts" are in the PR.
4. For `sim`, the PR also carries the class diagram (spec §8). Run the §8
   self-review ("can a consumer understand the package without reading its
   internals? can the internals change without breaking consumers?") before
   requesting merge.
5. After each stage, tick its boxes here and push.

---

## Stage 0 — Project scaffold

**Goal:** an installable empty package with lint / type / test / CI all green, so
every later stage has a gate to pass.

### Tasks

- [ ] `pyproject.toml`: `uv`-managed, `src/` layout, `requires-python = ">=3.11,<3.12"`,
      project name `ridepulse`, console script `ridepulse = "ridepulse.cli:app"`.
      Core deps: `typer`, `pydantic>=2`. Dev extra: `pytest`, `pytest-cov`,
      `ruff`, `mypy`, `pre-commit`. Optional `geo` extra: `geopandas`, `shapely`.
- [ ] `src/ridepulse/__init__.py` with `__version__`.
- [ ] `src/ridepulse/cli.py`: `typer.Typer()` app with empty sub-apps `data`,
      `sim`, `forecast`, `serve` registered; `ridepulse --help` lists them.
- [ ] Tooling config in `pyproject.toml`: `[tool.ruff]` (line length, rule set),
      `[tool.mypy]` (`strict = true`, `mypy_path = "src"`), `[tool.pytest.ini_options]`
      (`testpaths = ["tests"]`, `--cov=ridepulse`).
- [ ] `.pre-commit-config.yaml`: `ruff` (lint + format), `mypy`,
      `nbstripout`, trailing-whitespace, end-of-file-fixer, check-yaml.
- [ ] `Makefile` with targets (stubs where the command does not exist yet):
      `setup` (`uv sync --all-extras`), `lint`, `format`, `typecheck`, `test`,
      `data`, `sim`, `train`, `backtest`, `serve`, `loadtest`, `smoke`,
      `report`, `clean`.
- [ ] `.github/workflows/ci.yml`: on push + PR — `uv sync --all-extras`, then
      `make lint typecheck test`. Cache the `uv` env.
- [ ] `configs/README.md` explaining the `configs/{sim,forecast}/` layout.
- [ ] `docs/adr/0000-record-architecture-decisions.md`: the ADR process + template
      (Michael Nygard format).
- [ ] `tests/conftest.py`: shared fixtures dir path helper (`FIXTURES = Path(__file__).parent / "fixtures"`).
- [ ] `tests/test_smoke_import.py`: `import ridepulse` and `ridepulse.cli.app`
      resolve; `ridepulse --help` exit code 0 (via `typer.testing.CliRunner`).
- [ ] Update root `README.md` status line to "implementation in progress — Phase 0".

### Automated verification

- [ ] `uv sync --all-extras` succeeds from a clean checkout.
- [ ] `make lint typecheck test` all green locally and in CI.
- [ ] `ridepulse --help` shows the four sub-apps.

### Mergeable when

CI is green on the PR; ADR-0000 present.

---

## Stage 1 — `data` package

**Goal:** `make data` reproduces the demand and ETA feature tables from a
checksummed manifest, with pandera gating every stage.

### Design artifacts

- [ ] `docs/adr/0001-data-pipeline-and-repository.md`: DuckDB out-of-core choice;
      pandera-as-gate; the **Repository pattern** boundary (`ParquetRepository`)
      isolating parquet + paths from consumers (spec §8); cleaning rules recorded
      as explicit modeling assumptions. Alternatives considered (pandas chunking,
      Polars, a warehouse).
- [ ] `docs/data-dictionary.md`: every column of every emitted table — name,
      dtype, semantics, null policy — and each cleaning rule with its rationale.

### Tasks

- [ ] `manifests/tlc_2023.yaml`: schema = list of `{name, url, sha256, kind}`
      entries for `yellow_tripdata_2023-01.parquet`, `yellow_tripdata_2023-02.parquet`,
      `taxi_zone_lookup.csv`, `taxi_zones.zip` (shapefile). Leave `sha256: null`
      initially.
- [ ] Test `tests/data/test_manifest.py`: a valid fixture manifest parses into the
      pydantic `Manifest` model; a manifest with a missing `url` or bad `kind`
      raises. → implement `src/ridepulse/data/manifest.py` (`Manifest`,
      `ManifestEntry`, `load_manifest(path)`, `entry(name)`).
- [ ] Test `tests/data/test_download.py`: downloading a local `file://` fixture
      verifies its SHA-256; a deliberately wrong expected checksum raises
      `ChecksumMismatch`; a truncated partial file resumes to completion.
      → implement `src/ridepulse/data/download.py` (`fetch(entry, dest, *, resume=True)`,
      `verify_checksum(path, sha256)`; loud failure, no silent skip).
- [ ] Task: `ridepulse data download --manifest manifests/tlc_2023.yaml` — fetch
      all entries, then **print the computed SHA-256 for each**. Run once, paste
      the real checksums back into the manifest, commit.
- [ ] Test `tests/data/test_schemas.py`: each pandera schema accepts a good
      fixture row set and rejects a bad one (wrong dtype; `PULocationID` = 300;
      negative duration). → implement `src/ridepulse/data/schemas.py`:
      `RawYellowTripSchema`, `CleanedTripSchema`, `DemandFeatureSchema`,
      `EtaFeatureSchema`.
- [ ] Test `tests/data/test_clean.py`: a hand-built ~40-row raw parquet fixture,
      one row per cleaning rule, → a known cleaned frame. Rules: drop pickup ts
      outside the target month; drop duration ≤ 0 or > 180 min; drop
      `trip_distance` ≤ 0 or > 100 mi; drop `PU/DOLocationID` not in 1..263 (drops
      264/265/null); dedupe exact duplicates. → implement
      `src/ridepulse/data/clean.py` (`clean_month(raw_path, month, out_path)`),
      DuckDB SQL only, never a full month into pandas. pandera-validate the output.
- [ ] Test `tests/data/test_features_demand.py`: fixture of 3 zones × 12 hours of
      cleaned trips → hand-computed pickup counts; assert dense zero-filled grid
      (every zone × every hour in range present); assert calendar columns; assert
      `lag_1h` / `lag_24h` / `lag_168h` and `roll_mean_24h` / `roll_mean_168h`
      match hand math. **Leakage assertion**: row at ts `t` has `lag_1h` equal to
      the count at `t-1h`, never at `t` or later. → implement
      `src/ridepulse/data/features_demand.py` (`build_demand_features(cleaned_path, out_path)`).
      Lags/rolls computed per zone, time-ordered, shifted so row `t` uses only
      `< t`. US holidays via the `holidays` package.
- [ ] Test `tests/data/test_features_eta.py`: fixture → `duration_min` computed
      from pickup/dropoff; feature columns present (`PULocationID`, `DOLocationID`,
      `hour`, `dow`, `trip_distance`, `passenger_count`); the time-ordered
      train/holdout split has no timestamp overlap. → implement
      `src/ridepulse/data/features_eta.py` (`build_eta_features(cleaned_path, out_path)`).
- [ ] Test `tests/data/test_repository.py`: `ParquetRepository.write("demand_features", df)`
      then `.read("demand_features")` round-trips; unknown logical name raises;
      `.path("demand_features")` returns the resolved path. → implement
      `src/ridepulse/data/repository.py` (`ParquetRepository(root)` with a
      logical-name → relative-path registry).
- [ ] Wire CLI: `ridepulse data build --months 2023-01..2023-02` runs
      download → validate → clean → features (demand + eta), writing via
      `ParquetRepository`. Sub-commands `download`, `validate`, `clean`, `features`
      for partial runs.
- [ ] `Makefile`: `data:` → `ridepulse data build --months 2023-01..2023-02`.
- [ ] `tests/fixtures/data/`: commit the tiny raw / cleaned / feature parquet
      fixtures used above. Add `scripts/sample_fixtures.py` (documented) that
      regenerates them from a random slice of the real download.
- [ ] Test `tests/data/test_pipeline_fails_loud.py`: injecting a schema-violating
      row into a clean-stage input makes `data build` exit non-zero with a pandera
      error (spec §10 "fails loudly").

### Automated verification

- [ ] `pytest tests/data` green, including the leakage assertion and the
      fail-loud test.
- [ ] `make data` on the real 2-month download produces
      `data/processed/demand_features.parquet` (~372k rows: 263 zones × ~1416
      hours) and `data/processed/eta_features.parquet`, both pandera-valid.
- [ ] Re-running `make data` is idempotent (same row counts, same checksums).

### Manual verification

- [ ] Spot-check a known-busy zone/hour (e.g. zone 161, a weekday 18:00) has a
      plausible pickup count; a rarely-used zone is near zero, not missing.

### Mergeable when

CI green; ADR-0001 + data dictionary in the PR.

---

## Stage 2 — `sim.core` package

**Goal:** the shared city model that both simulators consume — grid, zone map,
TLC-calibrated demand profile, entity types — fixed now so Phase 6 needs no
redesign (spec §14 Phase 0).

### Design artifacts

- [ ] `docs/adr/0001-...` is `data`'s; create **`docs/adr/0002-sim-core-des-mdp-split.md`**
      — the spec §8 headline ADR. Must justify: why two simulators; what each
      optimizes (`des`: event-accurate, arbitrary distributions, per-rider
      metrics, agent what-ifs + the 4a A/B study; `mdp`: fixed Δt, vectorized,
      low-dim state, 10⁵–10⁷ steps for RL); how they stay consistent (shared
      `sim.core`; automated aggregate consistency test — written now, active in
      Phase 6); the chosen class model; the layered-core + Template-Method pattern.
      Alternatives: one simulator with two modes; two fully separate codebases.
- [ ] `docs/lld/sim-class-diagram.md`: mermaid class diagram — `sim.core` entities
      and interfaces (extended with `des` classes in Stage 3).

### Tasks

- [ ] `scripts/build_zone_geometry.py` (needs the `geo` extra): read `taxi_zones`
      shapefile → zone centroids → a 263×263 great-circle distance matrix. Write
      `src/ridepulse/sim/core/data/zone_centroids.parquet` and
      `zone_distances.npy`. **Commit both** (≈ 0.6 MB).
- [ ] Test `tests/sim/core/test_grid.py`: distance matrix is symmetric,
      zero on the diagonal, all finite; `travel_time(a, b, speed_kmh)` is
      monotonic in distance and `travel_time(a, a) == 0`. → implement
      `src/ridepulse/sim/core/grid.py` (`CityGrid.load()`, `.distance_km(a, b)`,
      `.travel_time_min(a, b, speed_kmh)`).
- [ ] Test `tests/sim/core/test_zones.py`: 263 zones load; `id → name → borough`
      lookups round-trip; an out-of-range id raises. → implement
      `src/ridepulse/sim/core/zones.py` (`ZoneMap.load(lookup_csv)`).
- [ ] Test `tests/sim/core/test_demand.py`: calibrated `arrival_rate(zone, ts)`
      is non-negative and finite for every zone across a full week; total
      simulated daily arrivals for a sample zone are within a documented
      tolerance (e.g. ±15%) of that zone's real mean daily pickups; identical
      under a fixed seed. → implement `src/ridepulse/sim/core/demand.py`
      (`DemandProfile.calibrate(cleaned_trips_path)` → artifact;
      `DemandProfile.from_artifact(path)`; `.arrival_rate(zone_id, timestamp)`
      returns riders/min from the (zone × hour-of-week) Poisson table; `.sample_arrivals(zone, t0, t1, rng)`).
- [ ] Test `tests/sim/core/test_entities.py`: `Rider` / `Driver` state-machine
      transitions — only legal transitions allowed, illegal ones raise. → implement
      `src/ridepulse/sim/core/entities.py` (`Rider`, `Driver` frozen-ish
      dataclasses; `RiderState`, `DriverState` enums; `Assignment`).
- [ ] Test `tests/sim/core/test_city.py`: `CityModel.build(config)` is
      deterministic for a fixed seed; exposes `.grid`, `.zones`, `.demand`.
      → implement `src/ridepulse/sim/core/city.py` (`CityModel`, `CityConfig`).
- [ ] Wire CLI: `ridepulse sim calibrate --months 2023-01..2023-02 --out configs/sim/demand_profile.parquet`.
- [ ] `configs/sim/baseline.yaml`: `n_drivers`, initial driver distribution
      (uniform or demand-weighted), sim horizon, seed, demand-profile artifact
      path, dispatch policy name + params (`radius_km`) — consumed in Stage 3.

### Automated verification

- [ ] `pytest tests/sim/core` green, including the calibration-fidelity test.
- [ ] `ridepulse sim calibrate` produces the demand-profile artifact from the
      Stage 1 cleaned trips.

### Mergeable when

CI green; ADR-0002 + class diagram in the PR; §8 self-review done.

---

## Stage 3 — `sim.des` package (+ `sim.mdp` stub)

**Goal:** a discrete-event simulator on `sim.core` that runs a scenario and emits
an event log, with a pluggable `DispatchPolicy` and conservation invariants held
under test. `sim.mdp` interface stub only.

### Design artifacts

- [ ] Extend `docs/adr/0002-...` (or add `docs/adr/0003-des-dispatch-strategy.md`)
      with: the **Strategy + ABC** for `DispatchPolicy`; the **Observer** pattern
      for the event stream (event log, metrics collector, future monitoring
      subscribe independently); why SimPy.
- [ ] Extend `docs/lld/sim-class-diagram.md` with `Simulation`, `DispatchPolicy`,
      `EventObserver`, `EventLog`, `MetricsCollector`.

### Tasks

- [ ] Test `tests/sim/des/test_events.py`: each event dataclass carries its
      fields; `EventLog.append(...)` then `.to_frame()` / `.to_parquet(path)` /
      `EventLog.from_parquet(path)` round-trips. → implement
      `src/ridepulse/sim/des/events.py` (`RiderRequested`, `RiderMatched`,
      `RiderCancelled`, `PickupCompleted`, `TripCompleted`, `DriverRepositioned`;
      `EventLog`).
- [ ] Test `tests/sim/des/test_dispatch.py`: on a hand-built set of pending
      riders + idle drivers, `NearestDriverPolicy` assigns each rider its closest
      idle driver within `radius_km`; a rider with no driver in radius stays
      unassigned and is served FIFO once one frees up; no driver double-assigned.
      → implement `src/ridepulse/sim/des/dispatch.py` (`DispatchPolicy` ABC with
      `assign(pending, idle, city, now) -> list[Assignment]`; `NearestDriverPolicy`;
      `POLICIES` registry mapping name → class).
- [ ] Test `tests/sim/des/test_observers.py`: after a run, `MetricsCollector`
      totals (rides completed, cancellations, mean/median/p90 wait, driver idle %)
      equal an independent recomputation from the raw `EventLog`. → implement
      `src/ridepulse/sim/des/observers.py` (`EventObserver` ABC;
      `MetricsCollector`; `EventLogWriter`) and `src/ridepulse/sim/des/metrics.py`
      (`summarize(event_log) -> SimMetrics`).
- [ ] Test `tests/sim/des/test_simulation.py`: a tiny scenario (5 drivers, 1 sim
      hour, fixed seed) runs and returns an `EventLog`; **the same seed produces a
      byte-identical event frame** on a re-run. → implement
      `src/ridepulse/sim/des/simulation.py` (`Simulation(config)`, `.run() -> EventLog`;
      SimPy `Environment`; processes: Poisson rider-arrival generator from
      `DemandProfile`, per-rider lifecycle request→wait→(match|cancel-on-patience)→
      pickup→dropoff→driver-idle, driver movement via `CityGrid.travel_time_min`).
- [ ] Test `tests/sim/des/test_invariants.py` (conservation — spec §11):
      over a full scenario run — every rider ends in exactly one terminal state
      (completed XOR cancelled); driver count is constant; no driver occupies two
      states at once; no `TripCompleted` precedes its `PickupCompleted`; every
      `RiderMatched` had a genuinely idle driver at match time.
- [ ] `src/ridepulse/sim/mdp/interface.py`: **stub only** — `MdpSimulator`
      `Protocol` / ABC with `reset(seed) -> State`, `step(state, action) -> tuple[State, float, bool, dict]`,
      placeholder `State` / `Action` types, full docstrings pointing to Phase 6.
      Method bodies `raise NotImplementedError`.
- [ ] Test `tests/sim/mdp/test_stub.py`: the interface imports; instantiating /
      calling `step` raises `NotImplementedError`.
- [ ] Test `tests/sim/test_des_mdp_consistency.py`: **write the assertion now,
      mark `@pytest.mark.skip(reason="sim.mdp implemented in Phase 6")`** — same
      scenario + seed, `des` and `mdp` agree on aggregate demand served and mean
      wait within a documented tolerance.
- [ ] Wire CLI: `ridepulse sim run --config configs/sim/baseline.yaml --out reports/sim/baseline/`
      → writes `event_log.parquet` + `metrics.json`.
- [ ] `Makefile`: `sim:` → `ridepulse sim run --config configs/sim/baseline.yaml --out reports/sim/baseline/`.

### Automated verification

- [ ] `pytest tests/sim` green — invariants, determinism, dispatch, observers,
      mdp stub. Consistency test collected but skipped.
- [ ] `make sim` produces `reports/sim/baseline/event_log.parquet` and
      `metrics.json`.
- [ ] CI includes the conservation-invariant tests.

### Manual verification

- [ ] Open `reports/sim/baseline/metrics.json` — median wait, cancellation rate,
      driver idle % are in plausible ranges for the configured fleet size.

### Mergeable when

CI green; ADR + updated class diagram in the PR; §8 self-review done.
**This completes spec §14 Phase 0's "Done" gate.**

---

## Stage 4 — `forecast` package (model + backtest)

**Goal:** a demand model with a leakage-asserted rolling-origin backtest,
calibrated prediction intervals, and MLflow registry integration — the modeling
core of Phase 1.

### Design artifacts

- [ ] `docs/adr/0004-forecast-model-interface.md`: the **Protocol / Template-Method**
      `ForecastModel` contract and shared backtest scaffold (spec §8);
      global-model-over-all-zones vs per-zone; interval method choice
      (why split-conformal over native quantile / bootstrap — D10); registry
      accessed **behind the Repository seam** so `serving` depends only on the
      interface. Alternatives considered.

### Tasks

- [ ] Test `tests/forecast/test_dataset.py`: from a fixture demand feature table,
      `assemble(...)` returns aligned `X` / `y` / `ts`; no NaN in required
      features after the lag/rolling warmup period is dropped. → implement
      `src/ridepulse/forecast/dataset.py`.
- [ ] Test `tests/forecast/test_backtest_integrity.py` (spec §11 — **the leakage
      test**): on synthetic time-indexed data, every fold from
      `RollingOriginBacktest` satisfies `max(train_ts) < min(test_ts)`; a
      deliberately overlapping fold spec raises `LeakageError`. → implement the
      guard inside `src/ridepulse/forecast/backtest.py`.
- [ ] Test `tests/forecast/test_backtest.py`: expanding weekly folds have correct
      boundaries (train ≥ 3 weeks, roll weekly); per-fold **MAE / MAPE / bias**
      match hand values on the Appendix A.1 series (actual `[100,140,160,120]`,
      forecast `[90,100,110,105]` → MAE 28.75, MAPE 20.6%, bias −28.75). → implement
      `RollingOriginBacktest.split(ts)` and `score_fold(...)`.
- [ ] Test `tests/forecast/test_intervals.py`: split-conformal on synthetic data
      yields empirical coverage ≈ nominal; `coverage_report(forecasts, actuals, nominal=0.8)`
      returns `observed_coverage`, `gap_pp`, `pass` — passes at the Appendix A.3
      case (612/720 = 85.0% vs 80% → +5.0 pp → pass, flagged) and fails at a
      +7 pp case. → implement `src/ridepulse/forecast/intervals.py`
      (`SplitConformal.calibrate(residuals, alpha)`, `.interval(point)`).
- [ ] Test `tests/forecast/test_model_lightgbm.py`: `LightGBMForecaster.train(cfg)`
      on the fixture demand table finishes in seconds; `predict(zone, ts, horizon)`
      returns a `DemandForecast` with `lower ≤ point ≤ upper` for every step;
      deterministic under a fixed seed. → implement
      `src/ridepulse/forecast/model.py`: `ForecastModel` Protocol
      (`train(cfg)`, `predict(zone, ts, horizon) -> DemandForecast`),
      `BaseForecaster` Template-Method holding the backtest scaffold,
      `LightGBMForecaster` (global model; point forecast + split-conformal
      interval; also fits q=0.1 / q=0.9 quantile models for the comparison
      column).
- [ ] Test `tests/forecast/test_baselines.py`: `SeasonalNaiveForecaster.predict`
      returns the observed value 168 h earlier. → implement it (plus optionally a
      thin `statsforecast` wrapper — `SeasonalNaive` at minimum).
- [ ] Test `tests/forecast/test_registry.py` (against a tmp `mlruns/`):
      `ModelRegistry.log_model(model, metrics, params, tags)` then `.load(name)`
      round-trips a working model; `.promote(version, "Production")` changes stage;
      `.load(name, stage="Production")` returns the promoted version. → implement
      `src/ridepulse/forecast/registry.py` wrapping `mlflow` (local file backend).
- [ ] Test `tests/forecast/test_report.py`: `write_backtest_report(results, out_dir)`
      creates `methodology.md`, `metrics.json`, `folds.csv` and at least one PNG.
      → implement `src/ridepulse/forecast/report.py`.
- [ ] `configs/forecast/lightgbm.yaml` + `configs/forecast/seasonal_naive.yaml`:
      feature list, hyperparams, backtest window / fold spec, interval nominal
      level, calibration-slice fraction.
- [ ] Wire CLI: `ridepulse forecast train --config ...` (train on all data, log +
      register to MLflow); `ridepulse forecast backtest --config ...` (rolling
      backtest → `reports/backtest/`, log folds to MLflow).
- [ ] `Makefile`: `train:` and `backtest:` targets.

### Automated verification

- [ ] `pytest tests/forecast` green — leakage test, hand-checked metric values,
      interval coverage, registry round-trip.
- [ ] `make backtest` writes `reports/backtest/methodology.md` + `metrics.json` +
      `folds.csv`; the leakage assertion runs for every fold and passes on real
      data.
- [ ] `make train` registers a model version in `mlruns/` and promotes it to
      Production.

### Manual verification

- [ ] Read `reports/backtest/methodology.md`: rolling-origin scheme, leakage
      guard, interval method are all described. MAE magnitude is plausible (tens
      of pickups/hour for busy zones); interval coverage is within ±5 pp of
      nominal or the gap is flagged.
- [ ] LightGBM beats seasonal-naive on aggregate MAE (or the gap is explained).

### Mergeable when

CI green; ADR-0004 + `reports/backtest/` artifact in the PR.

---

## Stage 5 — `serving` package (`/forecast` API)

**Goal:** a FastAPI service that loads the Production forecast model from the
registry and answers `/forecast` with prediction intervals, structured logging,
`model_version` + `request_id` on every response, Dockerized and in
`docker-compose.yml`, with a recorded load-test result.

### Design artifacts

- [ ] `docs/adr/0005-serving-design.md`: app-factory + load-model-from-registry-at-startup;
      sync vs async handlers; the `422` / `503` error-code contract (spec §10);
      structured-JSON logging approach; **load-test-as-artifact, not CI gate**
      (spec §10). Alternatives considered.

### Tasks

- [ ] Test `tests/serving/test_schemas.py`: `ForecastRequest` accepts a valid
      body; rejects `zone_id` 0 / 264, `horizon_hours` 0 / 200, a non-ISO
      timestamp → pydantic `ValidationError` (surfaced as `422`). → implement
      `src/ridepulse/serving/schemas.py` (`ForecastRequest`, `ForecastResponse`
      with `points: list[ForecastPoint]`, `model_version`, `request_id`).
- [ ] Test `tests/serving/test_routes.py` (`fastapi.testclient`): with a tiny
      model loaded into a tmp registry, `POST /forecast` → `200` + response shape
      + non-empty `model_version` + a `request_id`; `GET /healthz` → `200` with
      `model_version`; with an **empty** registry, `/forecast` → `503`. → implement
      `src/ridepulse/serving/app.py` (`create_app()`), `routes.py` (`/forecast`,
      `/healthz`).
- [ ] Test `tests/serving/test_middleware.py`: every response carries a unique
      `request_id`; `latency_ms` is recorded. → implement
      `src/ridepulse/serving/middleware.py`.
- [ ] Test `tests/serving/test_logging.py`: one request emits exactly one
      parseable JSON log line containing `request_id`, `zone_id`, `latency_ms`,
      `model_version`, `status`. → implement `src/ridepulse/serving/logging.py`.
- [ ] Test `tests/serving/test_contract.py` (spec §11 contract test): the app's
      generated OpenAPI schema equals the committed
      `docs/openapi/forecast.json` snapshot; on mismatch the test message says how
      to regenerate. → commit the snapshot; implement the comparison.
- [ ] `src/ridepulse/serving/loadtest/locustfile.py` + `run_loadtest.sh`: drive
      `/forecast` at a fixed RPS for N seconds, parse latencies, write
      `reports/loadtest/forecast.md` with p50 / p90 / p99 (p99 index =
      `ceil(0.99 · n)`, per Appendix A.16), achieved RPS, and PASS/FAIL vs the
      100 ms p99 budget.
- [ ] `serving/Dockerfile`: `python:3.11-slim`, `uv` install of the project,
      `uvicorn ridepulse.serving.app:create_app --factory`.
- [ ] `docker-compose.yml`: `serving` service — build context `.`, port `8000`,
      volumes for `mlruns/` and `data/processed/`, healthcheck on `/healthz`.
- [ ] Wire CLI + Make: `ridepulse serve` (local uvicorn); `make serve`,
      `make loadtest`.

### Automated verification

- [ ] `pytest tests/serving` green — schema validation, `200` / `422` / `503`
      paths, contract snapshot, logging shape.
- [ ] `docker compose up serving` starts; `/healthz` returns `200` with a
      `model_version`.

### Manual verification

- [ ] `curl` the reference-scenario request (zone 161, a rainy-evening timestamp,
      `horizon_hours: 3`) → a forecast with per-hour `yhat` / `yhat_lower` /
      `yhat_upper`, a `model_version`, and a `request_id`.
- [ ] `make loadtest` → `reports/loadtest/forecast.md` exists with a p99 number
      and an explicit PASS/FAIL against 100 ms (either outcome is acceptable — a
      breach is a recorded finding).

### Mergeable when

CI green; ADR-0005 + `reports/loadtest/forecast.md` in the PR.

---

## Stage 6 — Integration (E2E smoke + Phase 1 wrap)

**Goal:** one command takes a clean checkout to a live forecast; CI proves it on
a sampled slice.

### Tasks

- [ ] `scripts/smoke.sh` (and `make smoke`): sampled slice → `ridepulse data build`
      → `ridepulse forecast train` (+ register) → start `serving` →
      3 `/forecast` calls → assert response shapes and that `model_version` is
      populated. Non-zero exit on any failure.
- [ ] `tests/e2e/test_smoke.py` marked `@pytest.mark.e2e`: the programmatic
      version of the above, runnable in CI on a **committed tiny sample**
      (`tests/fixtures/e2e/`).
- [ ] `.github/workflows/ci.yml`: add a `smoke` job running `make smoke` on the
      committed sample.
- [ ] `README.md`: Phase 0 + Phase 1 sections — the architecture slice built so
      far, and copy-paste `make data` / `make sim` / `make backtest` /
      `make serve` commands with expected output. Update status.
- [ ] `docs/skills-map.md`: first entries mapping talking points to artifacts —
      reproducible checksummed pipeline; leakage-asserted rolling-origin backtest;
      split-conformal intervals with a calibration check; Repository / Strategy /
      Observer / Template-Method seams with their ADRs; SLO load test; structured
      request logging; `sim.des` conservation invariants.
- [ ] Verify from a fresh clone: `make setup && make smoke` succeeds.

### Automated verification

- [ ] `make smoke` green locally and as a CI job.
- [ ] Full `pytest` (unit + `-m e2e`) green.

### Manual verification

- [ ] Follow the README Phase 0–1 sections top to bottom on a clean checkout;
      every command behaves as documented.

### Mergeable when

CI green (lint, typecheck, unit, smoke); README + `docs/skills-map.md` updated.
**This completes spec §14 Phase 1's "Done" gate.**

---

## Definition of done for this plan

- [ ] Spec §14 **Phase 0 Done**: `make data` reproduces all feature tables from
      the manifest; `sim.des` runs a scenario and emits an event log; unit tests +
      conservation invariants green in CI.
- [ ] Spec §14 **Phase 1 Done**: the live API returns forecasts with intervals;
      `reports/backtest/` contains the methodology write-up; the load-test result
      is recorded.
- [ ] ADRs 0000–0005 merged. `sim` class diagram merged.
- [ ] `docs/skills-map.md` has its Phase 0–1 entries.
- [ ] Seven PRs merged to `main`, each with its own green CI.

---

## Deferred increments (tracked, not in this plan)

1. **Full data scope** — green + FHV sources, 2023-01..2023-06, run on the
   M1 / Oracle box; re-run backtest and calibration; update `reports/`.
2. **Weather feature** — NOAA GHCN precip ingestion + `precip × hour` feature;
   before/after leakage-asserted backtest; the §1 "model underweights rain"
   narrative beat.
3. **`sim.mdp` implementation + consistency test** — Phase 6.
