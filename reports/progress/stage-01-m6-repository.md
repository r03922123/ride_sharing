# Stage 1 — M6 repository

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (10 files) · pytest 37 passed

## Done
- `src/ridepulse/data/repository.py` — `ParquetRepository(root)` with a
  `_REGISTRY` mapping logical names (`cleaned_trips`, `demand_features`,
  `eta_features`) → relative parquet paths. Methods: `path`, `exists`, `write`
  (mkdirs, `index=False`), `read` (raises `FileNotFoundError` if not built),
  `datasets`. Unknown name → `KeyError` listing known names.
- `tests/data/test_repository.py` — 5 tests: write→read round-trip
  (`assert_frame_equal`), unknown-name `KeyError`, `path()` resolves without
  writing, read-before-build `FileNotFoundError`, `datasets()` list.

## Decisions / deviations from plan
- Registry holds the three processed tables only; raw files stay with the
  download layer, CSV zone lookup is read directly where needed (repository is
  parquet-only).

## Blocked / deferred
- none.

## Next
- M7 cli-wire — `ridepulse data build --months 2023-01..2023-02` +
  `download`/`validate`/`clean`/`features` subcommands; `Makefile` `data:` target;
  `test_pipeline_fails_loud.py`.
