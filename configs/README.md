# configs/

Runtime configuration for the packages that need it, kept out of code so scenarios
and hyperparameters are versioned and diffable without touching `src/`.

- `configs/sim/` — simulation scenario configs (fleet size, driver distribution,
  horizon, seed, demand-profile artifact path, dispatch policy + params). Consumed
  by `ridepulse sim run --config ...` (Stage 3).
- `configs/forecast/` — model configs (feature list, hyperparameters, backtest
  window / fold spec, interval nominal level, calibration-slice fraction).
  Consumed by `ridepulse forecast train|backtest --config ...` (Stage 4).

Each config is a YAML file loaded into a pydantic model, so a bad config fails
loudly at parse time rather than mid-run.
