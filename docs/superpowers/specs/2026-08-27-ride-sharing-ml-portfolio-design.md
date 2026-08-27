# ride-pulse — Design Spec

**Date:** 2026-08-27
**Status:** Approved for implementation planning
**Author:** csam020410@gmail.com
**Revised 2026-08-27:** added Phase 6 (reinforcement learning for driver
repositioning) and the dual-simulator design (discrete-event + time-stepped MDP).

---

## 1. Purpose & context

`ride-pulse` is a phased portfolio project: an ML system for ride-sharing demand
intelligence built on public NYC TLC trip data. It serves forecasting / ETA
models behind APIs, exposes them to an LLM ops-assistant agent, and includes
three rigorous evaluation studies — a simulated online experiment, an agent
benchmark, and (Phase 6) off-policy evaluation of a reinforcement-learning
repositioning policy.

### Why this project exists

The author has 5 years of research-oriented ML experience (computer vision, text,
audio; deep learning modeling). The project is **not** meant to prove modeling
ability — the market already assumes that. It is a **deliberate gap-closing
exercise** targeting the skills the author has identified as weak and as current
market requirements:

| Gap | Where the project closes it |
| --- | --- |
| ML system design | Multi-service architecture, tool APIs, provider abstraction, service orchestration |
| ML engineering | Reproducible data pipelines, model registry, serving with SLOs, CI, containers, monitoring |
| Statistics / A/B testing design | Phase 4a: pre-registered simulated online experiment with power analysis, CUPED, pitfall demonstration |
| Time-series / demand forecasting | Phase 1: demand model with rolling-origin backtesting, prediction intervals, leakage assertions |
| LLM / agent development | Phase 3: LiteLLM-routed ReAct agent with tool orchestration and trace logging |
| Low-level / OOP design | Cross-cutting: explicit class design, ADRs, class diagrams, design patterns per seam (see §8) |
| Reinforcement learning *(learning goal, not a prior interview gap)* | Phase 6: driver-repositioning RL on a time-stepped MDP simulator, with off-policy evaluation as the headline deliverable. Unifies the evaluation theme — OPE is the conceptual bridge between the A/B test (7a) and the agent benchmark (7b) |

### Target employers (all foreigner-application-friendly, Tokyo)

The same repository pitches three ways:

| Cluster | Screens hardest for | Lead phases | Pitch framing |
| --- | --- | --- | --- |
| AI-first (Sakana, Turing, foreign big tech) | Agent orchestration, eval rigor, research→production | 3, 4b, 1 | "Agent + eval harness on a production ML backend" |
| Consumer platforms (Rakuten, Mercari, LINE Yahoo, CyberAgent, DeNA) | Forecasting/ranking, A/B testing culture, MLOps | 1, 4a, 2 | "Forecasting service with rigorous backtesting + a pre-registered online experiment" |
| Fintech / payments (PayPay, Rakuten Pay) | Low-latency serving, imbalanced classification, monitoring, scale | 1, 2 (with optional risk classifier) | "Sub-100ms served models with drift monitoring and load-tested throughput" |

The agent (Phase 3) is the only target-specific bet and is upside-only: headline
for AI-first firms, bonus for the rest. The RL phase (Phase 6) is similarly
upside-only and lands hardest with autonomous-driving / mobility-adjacent AI
firms (e.g. Turing).

---

## 2. Constraints & non-goals

### Hard constraints

- **Compute:** MacBook Air M1, 8 GB unified memory, no CUDA. Classical models
  (LightGBM, statsforecast, tabular/linear RL) must train on the M1 in minutes.
  The Phase 6 RL stretch (small-MLP DQN/PPO) is allowed up to a few hours per
  training run against the fast time-stepped simulator. No GPU deep learning; no
  RL from raw/high-dimensional observations.
- **Budget:** zero. No paid LLM APIs. LLM inference via free hosted OSS models
  with a local fallback.
- **Licensing:** every dependency open-source.

### Non-goals (YAGNI — explicitly out of scope)

- GPU deep learning / neural forecasting models.
- Real-time streaming infrastructure (Kafka, Flink, Spark).
- Kubernetes; any cloud-native orchestration.
- Autonomous **dispatch matching**. The rider↔driver matching policy stays
  heuristic (nearest-driver, radius-then-queue, batched assignment). RL is
  applied only to the separate *driver-repositioning* problem in Phase 6.
- Deep / large-scale RL: multi-agent RL, RL from raw observations, distributed
  rollouts. Phase 6 is deliberately small (tabular / linear core, small-MLP
  stretch) with the evaluation methodology as the deliverable, not a
  state-of-the-art result.
- Multi-city generalization. NYC only.
- A production frontend. One minimal Gradio panel for the agent demo only.
- Workflow orchestrators (Prefect / Dagster). A `Makefile` is honest at this
  scale; the docs note the upgrade path.

---

## 3. Architecture

All services containerized; one `docker compose up` brings the system up.

```
┌─────────────────┐     ┌──────────────────┐
│  data pipeline  │────▶│  parquet store   │  (local dir + DuckDB)
│  (batch, CLI)   │     └──────────────────┘
└─────────────────┘              │
        │                        ▼
        │              ┌──────────────────┐    ┌─────────────┐
        └─────────────▶│  training (CLI)  │───▶│ MLflow      │
                       └──────────────────┘    │ registry    │
                                │              └─────────────┘
                                ▼                     │
                       ┌──────────────────┐           │
                       │  model-serving   │◀──────────┘
                       │  (FastAPI)       │
                       │  /forecast /eta  │
                       │  /risk (opt)     │
                       └──────────────────┘
                          ▲                     ▲
                          │                     │
                          │        ┌────────────────────────┐
                          │        │   ops-assistant agent  │
                          │        │   (LiteLLM-routed)      │
                          │        └───────────┬────────────┘
                          │        tools       │
                          │      (serving +    ▼
                          │       sim.des)  ┌────────────────────┐
                          │                 │   eval harness     │
                          │                 │   4a  A/B study    │
                          │                 │   4b  agent bench  │
                          │                 │   OPE (Phase 6)    │
                          │                 └────────────────────┘
   ┌──────────────────────────────────────┐
   │ sim.core   shared city model:        │
   │            grid, zones, demand prof.  │
   ├──────────────────┬───────────────────┤
   │ sim.des          │ sim.mdp           │
   │ (SimPy,          │ (NumPy,           │
   │  event-driven)   │  time-stepped)    │
   └────────┬─────────┴─────────┬─────────┘
            │                   │
            ▼                   ▼
   ┌────────────────┐   ┌────────────────────────┐
   │ 4a  A/B study  │   │ rl                     │
   │ (uses sim.des) │   │  Gym env, repositioning│◀── consumes /forecast
   └────────────────┘   │  policies, OPE         │
                        └────────────────────────┘
        ┌──────────────────┐
        │  monitoring      │  Evidently reports on a schedule
        │  (drift, perf)   │
        └──────────────────┘
```

**Data flow:** raw TLC → cleaned parquet → feature builder → train → registry →
serving. Both simulators are built on a shared `sim.core` city model. The agent
calls serving + `sim.des` over HTTP. The `rl` package wraps `sim.mdp` in a
Gymnasium environment and consumes demand forecasts as state features. The eval
harness drives the agent, the A/B study (on `sim.des`), and off-policy evaluation
of RL policies (on `sim.mdp`), writing reports to `reports/`. Monitoring reads
serving request logs plus a reference dataset.

---

## 4. Components

Each is a separate Python package under `src/ridepulse/`, independently testable.
The three questions each package must answer in its module docstring: **what does
it do, how do you use it, what does it depend on.**

| Package | Responsibility | Primary interface | Key dependencies |
| --- | --- | --- | --- |
| `data` | Download, validate, clean TLC data; build zone×time feature tables | CLI: `ridepulse data build --months 2023-01..2023-06` → parquet | TLC parquet, DuckDB, pandera |
| `sim.core` | Shared city model: grid, NYC zone mapping, demand profiles calibrated to TLC data, driver/rider entities | `CityModel`, `DemandProfile`, entity dataclasses | numpy |
| `sim.des` | Discrete-event simulation on `sim.core`: riders spawn from the demand profile, drivers move, dispatch matching policy is pluggable. Used by the agent and the Phase 4a A/B study | `Simulation(config).run() -> EventLog`; `DispatchPolicy` ABC | SimPy, `sim.core` |
| `sim.mdp` | Time-stepped vectorized simulation on `sim.core`: fixed-interval steps, low-dimensional state, fast enough for 10⁵–10⁷ steps. Used only by `rl` | `step(state, action) -> (state, reward, done)` | numpy, `sim.core` |
| `rl` | Driver-repositioning RL: Gymnasium environment wrapping `sim.mdp`; repositioning `Policy` ABC (heuristic baselines + learned); tabular/linear Q-learning core, small-MLP DQN stretch; hand-implemented off-policy evaluation (IPS, SNIPS, doubly-robust) | `RepositionEnv` (Gym API), `train_agent(cfg)`, `ope_report(logged, target)` | gymnasium, cleanrl or stable-baselines3, torch, `sim.mdp`, `forecast` |
| `forecast` | Demand model (pickups per zone per hour): LightGBM + statsforecast baselines; rolling-origin backtest; prediction intervals | `train(cfg)`, `predict(zone, ts, horizon) -> DemandForecast` | lightgbm, statsforecast, mlflow |
| `eta` | Trip-duration regressor (LightGBM) | `train(cfg)`, `predict(features) -> EtaPrediction` | lightgbm, mlflow |
| `risk` *(optional)* | Cancellation / payment-risk binary classifier; calibration; threshold selection under class imbalance | `train(cfg)`, `predict_proba(features)`, `calibration_report()` | lightgbm, scikit-learn |
| `serving` | FastAPI app: `/forecast`, `/eta`, `/risk`, `/healthz`; loads models from registry; structured request logging; p99 latency budget 100 ms | OpenAPI schema | fastapi, uvicorn, mlflow |
| `agent` | Ops-assistant: LiteLLM client, tool definitions wrapping serving + sim, ReAct loop with optional reflection, full trace logging, response cache, request cap | `Agent.run(query: str) -> AgentResult` | litellm, ollama, the serving API |
| `eval` | 4a: experiment runner (assignment, metrics, CUPED, hypothesis tests). 4b: agent task suite, graders, ablation runner, leaderboard. Also the shared statistics toolkit (bootstrap CIs, hypothesis tests) reused by `rl`'s OPE | CLI: `ridepulse eval ab`, `ridepulse eval agent` | scipy, statsmodels, the agent + `sim.des` |
| `monitoring` | Scheduled Evidently drift / performance reports: live window vs. reference | CLI + HTML report | evidently |

---

## 5. Data

- **Source:** NYC TLC Trip Record Data (yellow + green + FHV), public parquet.
  Roughly 2–3 M rows per month.
- **Scope:** 6 months of 2023 to start (`2023-01` … `2023-06`).
- **M1 handling:** DuckDB for out-of-core SQL; never load a full month into
  pandas. Feature tables aggregate to zone (263 NYC taxi zones) × hour, giving
  ~1.1 M rows for 6 months — trivial to model.
- **Forecasting target:** pickup count per zone per hour.
  Features: calendar (hour, day-of-week, US holiday via `holidays`), lags
  (1 h, 24 h, 168 h), rolling means (24 h, 168 h). Weather (NOAA GHCN, free) is a
  stretch feature.
- **ETA target:** trip duration derived from pickup / dropoff timestamps.
  Features: PU/DO zone pair, hour, day-of-week, trip distance, passenger count.
- **Risk target (optional):** derived from the simulator (a rider whose wait
  exceeds a patience threshold cancels) or from FHV records lacking a dropoff.
  Whichever is used is documented explicitly as a modeling assumption.
- **Reproducibility:** `manifests/tlc_2023.yaml` holds source URLs plus SHA-256
  checksums. `make data` re-derives every downstream artifact from the manifest.
- **Schema validation:** pandera schemas gate every stage; validation failure is
  loud and stops the pipeline.

---

## 6. LLM access layer

- **Abstraction:** every agent LLM call goes through **LiteLLM** (OpenAI-compatible
  interface). The model is selected by the `RIDEPULSE_LLM` environment variable.
- **Primary backend (free, hosted, OSS weights):** Groq free tier —
  `llama-3.3-70b-versatile` or `qwen-2.5-32b`. Documented backup free providers:
  Google AI Studio (Gemini Flash free tier), Cerebras free tier, OpenRouter free
  models.
- **Local fallback (fully offline):** Ollama running `qwen2.5:3b` on M1 Metal.
  Lower quality, but proves the system runs with zero external dependencies — a
  deliberate talking point about provider abstraction and graceful degradation.
- **Fallback chain:** LiteLLM configured `Groq → (backup hosted) → Ollama local`.
  The eval harness records which backend served each call.
- **Cost / determinism control:** a hard per-run request cap plus a SQLite
  response cache in the agent, so eval runs are bounded and reproducible.

---

## 7. Evaluation methodology

### 7a — Simulated online experiment (consumer-platform emphasis)

One intervention, implemented as a `DispatchPolicy` (or a pricing rule) in
`sim.des`: e.g. a surge-pricing rule change **or** a dispatch-radius change.

Deliverables:

- **Pre-registration document** (`reports/ab-study/preregistration.md`):
  hypothesis, primary metric (e.g. rider wait time), guardrail metrics (driver
  idle %, cancellation rate), randomization unit (rider session), minimum
  detectable effect, power analysis → required sample size / simulated duration.
- **Analysis:** two-sample test with confidence intervals; **CUPED** variance
  reduction using pre-period covariates; reported effect with interpretation.
- **Pitfall demonstration:** empirically show how peeking / early stopping
  inflates the false-positive rate, using repeated simulated experiments under
  the null.

### 7b — Agent evaluation harness (AI-first emphasis)

- **Task suite:** ~50 tasks across four categories —
  1. single-tool factual ("demand forecast for zone 161 tomorrow 08:00"),
  2. multi-step ("compare this week's Midtown demand to last month, explain the gap"),
  3. what-if ("simulate +10% surge in zone 230, report the wait-time change"),
  4. refusal / uncertainty ("forecast demand in Osaka" → must decline; out of data scope).
- **Graders (programmatic):** tool-call correctness; numeric answer within
  tolerance of ground truth from the APIs; an LLM-judge (same free model) scoring
  explanation quality against a fixed rubric.
- **Ablation as experiment:** model (`qwen2.5:3b` local / `llama-3.3-70b` /
  `qwen-2.5-32b`) × prompt strategy (zero-shot / ReAct / ReAct + reflection).
  Report pass rates with bootstrap confidence intervals, latency, and cost.
  Uses the same statistical vocabulary as 7a.
- **Output:** `reports/agent-bench/leaderboard.md` + a blog post.

### 7c — Off-policy / offline evaluation (RL, Phase 6)

The headline deliverable of Phase 6 is the *evaluation methodology*, not beating
the heuristic. It is the conceptual bridge between 7a and 7b: all three estimate
the value of a policy from limited data.

- **Estimators, hand-implemented:** inverse propensity scoring (IPS),
  self-normalized IPS (SNIPS), and a doubly-robust estimator, each tested against
  a known-answer toy MDP.
- **Protocol:** collect logged trajectories from a stochastic behavior policy on
  `sim.mdp`; estimate the learned policy's return via OPE; compare to the true
  return obtained by actually running the learned policy in the simulator (the
  simulator makes ground truth available — that is the point of using one).
- **Reporting:** OPE estimates with bootstrap confidence intervals; bias vs. the
  true return; sensitivity to behavior-policy stochasticity and trajectory count.
- **Limitations section (required):** an explicit, frank account of why the
  simulator constrains what can be concluded, and what would be needed to trust
  the result on real operations.

---

## 8. Low-level / OOP design (explicit deliverable)

Class design is a **first-class deliverable**, not a byproduct. The `sim` package
is deliberately the classic "design a ride-sharing / dispatch system" OOP
interview question.

### Required design artifacts

- **ADR per non-trivial package** in `docs/adr/` (`sim`, `agent`, `forecast`,
  `serving`, `eval`, `rl`): the design decision, alternatives considered, chosen
  class model, and why. The `sim` ADR must justify the `core` / `des` / `mdp`
  split (why two simulators, what each optimizes for, how they stay consistent).
- **Mermaid class diagrams** in `docs/lld/` for `sim` and `agent` (entities,
  interfaces, relationships, key methods).
- **Interview-prep doc** `docs/lld/design-a-ride-sharing-backend.md`: a written
  whiteboard-style answer to the LLD interview prompt that reuses the project's
  real class model.

### Patterns to apply consciously (one per seam)

| Seam | Pattern | Rationale |
| --- | --- | --- |
| Dispatch matching policies (`sim.des`) | Strategy + ABC | Swap matching logic without touching the sim loop |
| Repositioning policies (`rl`) | Strategy + ABC | Heuristic baselines and learned policies share one `Policy` interface |
| RL environment (`rl`) | Adapter | `RepositionEnv` adapts `sim.mdp` to the Gymnasium API |
| Prompt strategies (`agent`) | Strategy | Zero-shot / ReAct / reflection are interchangeable |
| LLM provider access | Adapter (via LiteLLM) | Uniform interface over Groq / Ollama / others |
| Agent tools | Command + registry | Each tool is a self-describing invocable unit |
| Model interface (`forecast`/`eta`/`risk`) | Protocol / Template Method | Common `train` / `predict` contract; shared backtest scaffold |
| Two simulators on one domain (`sim.core`) | Layered core + Template Method | `des` and `mdp` reuse the same city model and demand profiles; divergence is a test failure |
| Sim event stream (`sim.des`) | Observer | Event log, metrics collectors, monitoring subscribe independently |
| Data / registry access | Repository | Isolate parquet + MLflow behind a narrow interface |
| OPE estimators (`rl`) | Strategy | IPS / SNIPS / doubly-robust behind one estimator interface |

### Design review gate

Each package PR includes its ADR and (for `sim` / `agent` / `rl`) its class diagram.
The self-review checks: can a consumer understand the package without reading its
internals? Can the internals change without breaking consumers? If not, the
boundaries are reworked before merge.

---

## 9. Tech stack (all OSS, all M1-native)

- **Language / env:** Python 3.11, `uv`.
- **Data:** DuckDB, pandas, pandera, pyarrow.
- **Modeling:** LightGBM, statsforecast, scikit-learn, scipy, statsmodels.
- **Experiment tracking:** MLflow (local file backend; no tracking server).
- **Serving:** FastAPI + uvicorn.
- **Simulation:** SimPy (`sim.des`); NumPy (`sim.mdp`).
- **RL (Phase 6):** Gymnasium; CleanRL (single-file reference implementations,
  chosen for readability + learning) or Stable-Baselines3; PyTorch (CPU / MPS,
  small MLPs only).
- **Agent:** LiteLLM, Ollama (local), Groq free tier (hosted).
- **Monitoring:** Evidently.
- **Orchestration:** `Makefile` + `docker compose`.
- **Load testing:** `hey` or `locust`.
- **Testing / quality:** pytest, pytest-cov, ruff, mypy, pre-commit.
- **CI:** GitHub Actions — lint, type-check, unit tests, E2E smoke on sampled data.
- **Demo UI:** Gradio (single file).
- **Docs:** MkDocs Material; blog posts cross-posted to Zenn / Medium.

---

## 10. Error handling & operational concerns

- **Serving:** pydantic request validation; `422` on bad input; `503` if a model
  is not loaded; every response carries `model_version` and `request_id`;
  structured JSON logs.
- **Latency budget:** p99 < 100 ms for `/forecast` and `/eta` on the M1. A load
  test in the repo proves or refutes it; a breach is a documented finding, not a
  hidden failure.
- **Agent:** per-tool timeout (5 s); max 8 reasoning steps; graceful "I couldn't
  determine that" on tool failure; full trace persisted for every run.
- **LLM provider outage:** LiteLLM fallback chain Groq → backup → Ollama local;
  the backend that served each call is recorded.
- **Data pipeline:** pandera validation fails loudly; partial downloads resume
  from the manifest.

---

## 11. Testing strategy

- **Unit:** every package. Feature builders tested against hand-computed
  fixtures. Both simulators tested for conservation invariants (no rider or
  driver vanishes). Graders tested on golden transcripts.
- **Simulator consistency test:** on an identical scenario and seed, `sim.des`
  and `sim.mdp` must agree on aggregate demand served and mean wait time within a
  documented tolerance — guards against the two implementations drifting apart.
- **RL environment tests:** Gymnasium API compliance (`check_env`); deterministic
  rollout under a fixed seed; reward and termination logic against hand-computed
  cases.
- **OPE estimator tests:** IPS / SNIPS / doubly-robust each recover the known
  true return on a small toy MDP within Monte Carlo error.
- **Backtest integrity test:** automated assertion that no future data leaks into
  any training fold (`max(train_ts) < min(test_ts)` per fold).
- **Contract tests:** serving OpenAPI schema snapshot; agent tool schemas
  validated against live serving responses.
- **E2E smoke (`make smoke`, runs in CI):** one month of sampled data → train →
  serve → three agent queries → assert response shapes.
- **Eval reproducibility:** fixed seeds; agent response cache; assert leaderboard
  numbers are stable across two consecutive runs.

---

## 12. Repository structure

```
ride-pulse/
├── Makefile                 # data, train, serve, smoke, eval, report
├── docker-compose.yml
├── pyproject.toml           # uv
├── manifests/tlc_2023.yaml  # source URLs + SHA-256 checksums
├── src/ridepulse/
│   ├── data/  forecast/  eta/  risk/
│   ├── sim/                 # core/ (shared model), des/ (SimPy), mdp/ (NumPy)
│   ├── rl/                  # Gym env, repositioning policies, OPE
│   ├── serving/  agent/  eval/  monitoring/
├── configs/                 # yaml per model, per sim scenario, per experiment
├── notebooks/               # EDA + narrative, nbstripout'd
├── tests/
├── reports/                 # generated: backtest, drift, ab-study, agent-bench
├── docs/
│   ├── adr/                 # architecture decision records
│   ├── lld/                 # class diagrams + interview-prep doc
│   ├── skills-map.md        # talking points mapped to concrete artifacts
│   └── (mkdocs site: architecture, blog drafts)
└── .github/workflows/ci.yml
```

---

## 13. Deployment & demo

- **Primary:** everything runs locally via `docker compose up`. README has
  copy-paste commands and expected output.
- **Public demo:** a free Hugging Face Space hosting the Gradio agent UI plus a
  lightweight serving instance (models are small). If a Space cannot run all
  services, fall back to a recorded walkthrough (asciinema / Loom) plus
  screenshots in the README — honest and common for portfolio projects.
- **Repo:** public GitHub. README carries the architecture diagram, per-phase
  demo GIFs, and a "what this demonstrates" section mapped to `docs/skills-map.md`.

---

## 14. Phased delivery plan

Each phase ends with: a merged PR, green CI, a `reports/` artifact (from Phase 1
on), an ADR (where §8 requires one), and a README section. Portfolio talking
points are written into `docs/skills-map.md` as work proceeds.

Phase 1 alone is a legitimate MLE portfolio piece. Phases 1 + 3 + 4b are the
AI-first-firm pitch. Phases 1 + 4a + 2 are the consumer-platform pitch. Phase 6
(RL) is an independent later extension, upside-only.

### Phase 0 — Data & simulation foundation

- TLC ingestion, checksum manifest, pandera schemas, cleaning to parquet.
- Feature builders for demand and ETA.
- `sim.core`: shared city model (grid, NYC zone mapping, demand profiles
  calibrated to real TLC patterns, driver/rider entities).
- `sim.des`: discrete-event simulator on `sim.core` with a pluggable
  `DispatchPolicy` ABC and a heuristic baseline policy.
- `sim.mdp` interface stub only (the fast time-stepped sim is built in Phase 6);
  Phase 0 fixes the `sim.core` boundary so Phase 6 does not force a redesign.
- ADR + class diagram for `sim` (must justify the `core` / `des` / `mdp` split).
- **Done:** `make data` reproduces all feature tables from the manifest; `sim.des`
  runs a scenario and emits an event log; unit tests + conservation invariants
  green in CI.

### Phase 1 — Forecasting service

- Demand model: LightGBM + statsforecast baselines.
- Rolling-origin backtest with leakage assertion; prediction intervals with a
  calibration check.
- MLflow registry integration.
- FastAPI `/forecast` endpoint with request validation, structured logs, and a
  p99 < 100 ms load test.
- Dockerized; added to `docker compose`.
- **Done:** live API returns forecasts with intervals; `reports/backtest/`
  contains the methodology write-up; load-test result recorded.

### Phase 2 — ETA model, optional risk classifier, monitoring

- ETA regressor (LightGBM) served at `/eta`.
- *(Optional, fintech focus)* imbalanced risk classifier at `/risk` with
  calibration curve, precision-recall analysis, threshold selection write-up.
- Evidently drift + performance monitoring comparing a live window to a reference
  dataset, on a schedule.
- **Done:** both/all models served; `reports/drift/` shows drift detected on a
  held-out later time period.

### Phase 3 — Ops-assistant agent

- LiteLLM-routed agent; tools wrap the Phase 1–2 APIs and `sim.des`.
- ReAct loop with optional reflection; response cache; request cap; trace
  logging.
- Local Ollama fallback verified.
- ADR + class diagram for `agent`.
- Minimal Gradio demo panel.
- **Done:** recorded walkthrough of an analyst asking, e.g., "why did demand
  spike in Midtown last Tuesday?" and getting a tool-grounded answer with a trace.

### Phase 4a — Simulated online experiment

- Pre-registration doc; intervention implemented as a `DispatchPolicy` / pricing
  change on `sim.des`.
- A/B run in `sim.des`; analysis with CIs + CUPED; peeking-pitfall
  demonstration.
- **Done:** `reports/ab-study/` contains pre-registration, analysis notebook, and
  a written conclusion.

### Phase 4b — Agent evaluation harness

- ~50-task suite; programmatic + LLM-judge graders.
- Model × prompt-strategy ablation with bootstrap CIs, latency, cost.
- **Done:** `reports/agent-bench/leaderboard.md` + blog post; numbers
  reproducible across two runs.

### Phase 5 — Polish

- Public repo, MkDocs site, architecture docs, `docs/skills-map.md` finalized.
- Three blog posts (forecasting rigor; agent + eval; system design + LLD).
- One-command `docker compose up` verified from a clean checkout.
- LLD interview-prep doc finalized.
- **Done:** a stranger can clone, run `docker compose up`, and reach the demo in
  under 15 minutes following the README.

### Phase 6 — Reinforcement learning for driver repositioning *(independent extension)*

- `sim.mdp`: fast time-stepped NumPy simulator on the Phase 0 `sim.core` model;
  the `sim.des` ↔ `sim.mdp` consistency test passes.
- `rl.RepositionEnv`: Gymnasium environment; state includes the current supply
  distribution, time-of-day, and the Phase 1 demand forecast; action is a
  repositioning assignment for idle drivers.
- Heuristic baseline policies (`stay-put`, `chase-forecast`).
- Learned policies: tabular / linear Q-learning (core); small-MLP DQN via CleanRL
  (stretch).
- Off-policy evaluation toolkit (§7c): IPS / SNIPS / doubly-robust, tested
  against a toy MDP, applied to compare policies without "deploying" them, then
  validated against true simulator returns.
- ADR + class diagram for `rl`.
- One blog post (RL + off-policy evaluation + honest limitations).
- **Done:** `reports/rl/` contains the training curves, the policy comparison
  table with bootstrap CIs, the OPE-vs-true-return bias analysis, and the
  limitations write-up; results reproducible across two runs.

---

## 15. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| 8 GB RAM thrash on data | DuckDB out-of-core; aggregate early; cap months |
| Groq free-tier rate limits during eval | Response cache; small task suite; Ollama local fallback |
| "Who actually uses this agent?" skepticism | Frame as internal ops/analytics assistant + what-if tool; never "autonomous dispatcher" |
| Simulator too toy to be credible | Calibrate demand to real TLC profiles; document assumptions and limitations explicitly |
| Scope creep across phases | Hard "done" definition per phase; each ships independently; Phase 1 alone is valid |
| OOP design done accidentally / poorly | §8: ADRs, class diagrams, conscious pattern per seam, design-review gate on every package PR |
| Dispatch-matching RL scope creep | Out of scope; matching stays heuristic. RL is confined to driver *repositioning* in Phase 6 |
| RL policy fails to beat the heuristic | Deliverable is the methodology (env design + OPE + honest analysis), not a win; a modest or null result is still a strong artifact |
| Simulator too toy for RL conclusions | Required limitations section in §7c; OPE reported with CIs and validated against true simulator returns |
| `sim.des` and `sim.mdp` drift apart | Shared `sim.core` domain model; automated consistency test on aggregate metrics |
| Small-MLP DQN training too slow on M1 | DQN is stretch-only; tabular/linear core trains in minutes; `sim.mdp` built for high step throughput |
| Public demo can't host all services | Recorded walkthrough + screenshots fallback, stated up front as acceptable |

---

## 16. Open questions (resolve during planning)

- Exact intervention for Phase 4a: surge-pricing rule vs. dispatch-radius change
  (pick one during Phase 0 once the simulator's behavior is observable).
- Whether the risk classifier label comes from the simulator or from FHV
  no-dropoff records (decide in Phase 2 based on which is more defensible).
- HF Space resource envelope: confirm it can host serving + Gradio together, else
  commit to the recorded-walkthrough fallback in Phase 5.
- Phase 6 RL state abstraction granularity: zone and time-bucket resolution for
  `sim.mdp` (coarser → tabular-feasible and faster; finer → more realistic but
  pushes toward the DQN stretch). Resolve at the start of Phase 6 once `sim.core`
  behavior is observable.
- Phase 6 ordering: whether to pull RL earlier if an autonomous-driving / mobility
  employer (e.g. Turing) becomes the primary target.
