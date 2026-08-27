# Stage 1 — M8 docs-pr

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (11 files) · pytest 40 passed

## Done
- `docs/adr/0001-data-pipeline-and-repository.md` — DuckDB out-of-core cleaning
  (pandas only for the ~372 k-row dense grid); pandera schemas as the loud gate;
  Repository seam; cleaning rules as modeling assumptions; alternatives
  (pandas chunking / Polars / warehouse) rejected with reasons.
- `docs/data-dictionary.md` — every column of `cleaned_trips`, `demand_features`,
  `eta_features`: dtype, semantics, null policy; the leakage and split
  guarantees; dow / timezone / index conventions.
- Manual spot check (real data): zone 161 (Midtown) Wed 18:00 = 378–618
  pickups/h (plausible rush hour); zone 5 (rare) = 0–1, mean 0.07 — present, not
  missing.

## PR
- `gh` is not installed on this machine — branch `stage/01-data` is pushed;
  open the PR from GitHub's "Compare & pull request" banner. Body: link ADR-0001
  + data dictionary + this milestone folder.

## Blocked / deferred
- none.

## Stage 1 result
All plan Stage 1 tasks complete. `make data` reproduces both feature tables from
the SHA-256-pinned manifest; ADR-0001 + data dictionary present; 40 tests green
(ruff + mypy strict clean). Ready to merge.
