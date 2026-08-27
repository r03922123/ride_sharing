# Stage 1 — M1 manifest-download

**Commit:** (this commit)
**Status:** done
**Gate:** ruff pass · mypy pass (5 files) · pytest 15 passed

## Done
- `src/ridepulse/data/manifest.py` — `ManifestEntry` (frozen, `extra=forbid`),
  `Manifest`, `load_manifest(path)`, `.entry(name)`, `.names()`.
  Guarded by `tests/data/test_manifest.py` (valid parse, unknown-name `KeyError`,
  missing-url / bad-kind `ValidationError`, non-list `ValueError`, real manifest valid).
- `src/ridepulse/data/download.py` — `sha256_of`, `verify_checksum`,
  `ChecksumMismatch`, `fetch(entry, dest, *, resume=True)` (handles `file://` and
  `http(s)://`, HTTP Range resume with restart-on-non-206), `fetch_all`,
  `computed_checksums`.
  Guarded by `tests/data/test_download.py` (checksum verify, wrong-checksum
  raises, truncated-file resume, no-resume restart, already-complete re-verify,
  no-checksum skip).
- `manifests/tlc_2023.yaml` — 4 entries (yellow 2023-01, 2023-02, zone lookup,
  zones shapefile). **Real download performed; SHA-256 for all four captured and
  committed.** Sizes: 47.7 MB, 47.7 MB, 12 KB, 1.0 MB. Re-fetch re-verifies OK.
- Test fixtures: `tests/fixtures/data/manifest_{ok,bad_kind,missing_url}.yaml`.
- `pyproject.toml`: added runtime deps (`duckdb`, `pandas`, `pyarrow`, `numpy`,
  `pandera`, `pyyaml`, `holidays`) and dev dep `types-PyYAML`.

## Decisions / deviations from plan
- `ruff` `N818` ignored project-wide: the plan pins the exception name
  `ChecksumMismatch` (and later `LeakageError`), which N818 would forbid. Noted
  inline in `pyproject.toml`.
- Tests reference fixtures via `Path(__file__).parents[1] / "fixtures"` rather
  than importing `tests.conftest` (`tests/` is not an import package).
- Data deps added to `[project.dependencies]` (core), not a `data` extra — the
  whole project is the pipeline; matches how the plan's later stages import them.

## Blocked / deferred
- none.

## Next
- M2 schemas — `data/schemas.py` pandera schemas + `tests/data/test_schemas.py`.
