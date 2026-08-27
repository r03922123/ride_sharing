from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ridepulse.data.repository import ParquetRepository


def test_write_then_read_round_trips(tmp_path: Path) -> None:
    repo = ParquetRepository(tmp_path)
    df = pd.DataFrame({"zone_id": [1, 2, 3], "pickups": [10, 20, 30]})

    written = repo.write("demand_features", df)
    assert written == tmp_path / "processed" / "demand_features.parquet"
    assert written.exists()

    back = repo.read("demand_features")
    pd.testing.assert_frame_equal(back, df)


def test_unknown_dataset_raises(tmp_path: Path) -> None:
    repo = ParquetRepository(tmp_path)
    with pytest.raises(KeyError, match="unknown dataset"):
        repo.path("nonsense")
    with pytest.raises(KeyError):
        repo.write("nonsense", pd.DataFrame())


def test_path_resolves_without_writing(tmp_path: Path) -> None:
    repo = ParquetRepository(tmp_path)
    p = repo.path("eta_features")
    assert p == tmp_path / "processed" / "eta_features.parquet"
    assert not repo.exists("eta_features")


def test_read_before_build_raises(tmp_path: Path) -> None:
    repo = ParquetRepository(tmp_path)
    with pytest.raises(FileNotFoundError, match="not built yet"):
        repo.read("cleaned_trips")


def test_datasets_lists_known_names() -> None:
    assert ParquetRepository.datasets() == [
        "cleaned_trips",
        "demand_features",
        "eta_features",
    ]
