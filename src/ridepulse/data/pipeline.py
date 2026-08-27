"""Orchestration: download -> clean -> features, wired to the CLI.

Every stage writes through :class:`ParquetRepository`. Any schema violation
raises out of here uncaught so the CLI exits non-zero (spec §10, "fails loudly").
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from ridepulse.data.clean import clean_month
from ridepulse.data.download import fetch_all
from ridepulse.data.features_demand import build_demand_features
from ridepulse.data.features_eta import build_eta_features
from ridepulse.data.manifest import load_manifest
from ridepulse.data.repository import ParquetRepository

DEFAULT_MANIFEST = Path("manifests/tlc_2023.yaml")


def parse_months(spec: str) -> list[str]:
    """``"2023-01..2023-03"`` -> ``["2023-01", "2023-02", "2023-03"]``; a bare
    ``"2023-01"`` -> ``["2023-01"]``."""
    if ".." not in spec:
        date.fromisoformat(f"{spec}-01")  # validate
        return [spec]
    lo, hi = (s.strip() for s in spec.split("..", 1))
    cur, end = date.fromisoformat(f"{lo}-01"), date.fromisoformat(f"{hi}-01")
    if end < cur:
        raise ValueError(f"empty month range: {spec}")
    out: list[str] = []
    while cur <= end:
        out.append(f"{cur.year:04d}-{cur.month:02d}")
        cur = (
            date(cur.year + 1, 1, 1)
            if cur.month == 12
            else date(cur.year, cur.month + 1, 1)
        )
    return out


def _raw_parquet(raw_dir: Path, month: str) -> Path:
    return raw_dir / f"yellow_tripdata_{month}.parquet"


def download_sources(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    raw_dir: str | Path = "data/raw",
) -> dict[str, Path]:
    manifest = load_manifest(manifest_path)
    return fetch_all(manifest.entries, Path(raw_dir))


def clean_months(
    months: list[str], raw_dir: str | Path, repo: ParquetRepository
) -> Path:
    """Clean each month, then concatenate into the ``cleaned_trips`` table."""
    raw_dir = Path(raw_dir)
    tmp_dir = repo.root / "processed" / "_months"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    for m in months:
        part = tmp_dir / f"cleaned_{m}.parquet"
        clean_month(_raw_parquet(raw_dir, m), m, part)
        parts.append(part.as_posix())

    out = repo.path("cleaned_trips")
    out.parent.mkdir(parents=True, exist_ok=True)
    array = "[" + ", ".join(f"'{p}'" for p in parts) + "]"
    con = duckdb.connect()
    try:
        con.execute(
            f"COPY (SELECT * FROM read_parquet({array}) ORDER BY pickup_ts) "  # noqa: S608
            f"TO '{out.as_posix()}' (FORMAT PARQUET)"
        )
    finally:
        con.close()
    return out


def build_features(repo: ParquetRepository) -> tuple[Path, Path]:
    cleaned = repo.path("cleaned_trips")
    if not cleaned.exists():
        raise FileNotFoundError(f"cleaned_trips not built: {cleaned}")
    demand = build_demand_features(cleaned, repo.path("demand_features"))
    eta = build_eta_features(cleaned, repo.path("eta_features"))
    return demand, eta


def build_all(
    months_spec: str,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    root: str | Path = "data",
) -> ParquetRepository:
    root = Path(root)
    months = parse_months(months_spec)
    download_sources(manifest_path, root / "raw")
    repo = ParquetRepository(root)
    clean_months(months, root / "raw", repo)
    build_features(repo)
    return repo
