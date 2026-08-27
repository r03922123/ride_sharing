from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from ridepulse.cli import app
from ridepulse.data.pipeline import clean_months, parse_months
from ridepulse.data.repository import ParquetRepository

runner = CliRunner()


def test_parse_months_range() -> None:
    assert parse_months("2023-01..2023-03") == ["2023-01", "2023-02", "2023-03"]
    assert parse_months("2023-11..2024-01") == ["2023-11", "2023-12", "2024-01"]
    assert parse_months("2023-05") == ["2023-05"]
    with pytest.raises(ValueError, match="empty month range"):
        parse_months("2023-03..2023-01")


def _raw_month(path: Path, month: str, n: int = 30) -> None:
    start = pd.Timestamp(f"{month}-05 08:00")
    rows = [
        {
            "tpep_pickup_datetime": start + pd.Timedelta(minutes=10 * i),
            "tpep_dropoff_datetime": start + pd.Timedelta(minutes=10 * i + 12),
            "PULocationID": 100 + i % 5,
            "DOLocationID": 200 + i % 5,
            "trip_distance": 1.5 + i % 3,
            "passenger_count": 1,
        }
        for i in range(n)
    ]
    pd.DataFrame(rows).to_parquet(path)


def test_clean_then_features_end_to_end(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for m in ("2023-01", "2023-02"):
        _raw_month(raw / f"yellow_tripdata_{m}.parquet", m)
    repo = ParquetRepository(tmp_path / "data")

    clean_months(["2023-01", "2023-02"], raw, repo)
    assert repo.exists("cleaned_trips")

    res = runner.invoke(app, ["data", "features", "--root", str(tmp_path / "data")])
    assert res.exit_code == 0, res.output
    assert repo.exists("demand_features")
    assert repo.exists("eta_features")

    vres = runner.invoke(app, ["data", "validate", "--root", str(tmp_path / "data")])
    assert vres.exit_code == 0, vres.output


def test_features_fails_loud_on_bad_cleaned_table(tmp_path: Path) -> None:
    repo = ParquetRepository(tmp_path / "data")
    bad = pd.DataFrame(
        {
            "pickup_ts": [pd.Timestamp("2023-01-02 08:00")],
            "dropoff_ts": [pd.Timestamp("2023-01-02 08:12")],
            "pu_location_id": [999],  # out of 1..263 -> schema violation
            "do_location_id": [200],
            "trip_distance": [2.0],
            "passenger_count": [1],
            "duration_min": [12.0],
        }
    )
    repo.path("cleaned_trips").parent.mkdir(parents=True, exist_ok=True)
    bad.to_parquet(repo.path("cleaned_trips"), index=False)

    res = runner.invoke(app, ["data", "features", "--root", str(tmp_path / "data")])
    assert res.exit_code != 0
