from pathlib import Path

import pytest
from pydantic import ValidationError

from ridepulse.data.manifest import Manifest, load_manifest

DATA_FIXTURES = Path(__file__).parents[1] / "fixtures" / "data"


def test_valid_manifest_parses() -> None:
    m = load_manifest(DATA_FIXTURES / "manifest_ok.yaml")
    assert isinstance(m, Manifest)
    assert m.names() == ["sample_parquet", "sample_lookup"]
    assert m.entry("sample_parquet").kind == "parquet"
    assert m.entry("sample_parquet").sha256 is None
    assert m.entry("sample_lookup").sha256 == "abc123"


def test_unknown_entry_name_raises() -> None:
    m = load_manifest(DATA_FIXTURES / "manifest_ok.yaml")
    with pytest.raises(KeyError):
        m.entry("does_not_exist")


def test_missing_url_raises() -> None:
    with pytest.raises(ValidationError):
        load_manifest(DATA_FIXTURES / "manifest_missing_url.yaml")


def test_bad_kind_raises() -> None:
    with pytest.raises(ValidationError):
        load_manifest(DATA_FIXTURES / "manifest_bad_kind.yaml")


def test_non_list_manifest_raises(tmp_path: Path) -> None:
    bad = tmp_path / "m.yaml"
    bad.write_text("entries: not-a-list\n")
    with pytest.raises(ValueError, match="must be a YAML list"):
        load_manifest(bad)


def test_real_manifest_is_valid() -> None:
    m = load_manifest(Path("manifests/tlc_2023.yaml"))
    assert "yellow_tripdata_2023-01" in m.names()
    assert all(e.url.startswith("https://") for e in m.entries)
