from pathlib import Path

import pytest

from ridepulse.data.download import (
    ChecksumMismatch,
    fetch,
    sha256_of,
    verify_checksum,
)
from ridepulse.data.manifest import ManifestEntry

CONTENT = b"ride-pulse test payload\n" * 100


def _source(tmp_path: Path) -> tuple[Path, str]:
    src = tmp_path / "source.parquet"
    src.write_bytes(CONTENT)
    return src, sha256_of(src)


def _entry(src: Path, sha256: str | None) -> ManifestEntry:
    return ManifestEntry(
        name="sample", url=src.as_uri(), sha256=sha256, kind="parquet"
    )


def test_fetch_verifies_checksum(tmp_path: Path) -> None:
    src, digest = _source(tmp_path)
    dest = tmp_path / "out" / "sample.parquet"
    result = fetch(_entry(src, digest), dest)
    assert result == dest
    assert dest.read_bytes() == CONTENT
    verify_checksum(dest, digest)


def test_fetch_wrong_checksum_raises(tmp_path: Path) -> None:
    src, _ = _source(tmp_path)
    bad = "0" * 64
    with pytest.raises(ChecksumMismatch):
        fetch(_entry(src, bad), tmp_path / "sample.parquet")


def test_fetch_resumes_truncated_file(tmp_path: Path) -> None:
    src, digest = _source(tmp_path)
    dest = tmp_path / "sample.parquet"
    dest.write_bytes(CONTENT[:512])  # simulate an interrupted download

    result = fetch(_entry(src, digest), dest, resume=True)

    assert result.read_bytes() == CONTENT
    verify_checksum(result, digest)


def test_fetch_no_resume_restarts(tmp_path: Path) -> None:
    src, digest = _source(tmp_path)
    dest = tmp_path / "sample.parquet"
    dest.write_bytes(b"garbage that is not a prefix")

    fetch(_entry(src, digest), dest, resume=False)

    assert dest.read_bytes() == CONTENT


def test_fetch_already_complete_reverifies(tmp_path: Path) -> None:
    src, digest = _source(tmp_path)
    dest = tmp_path / "sample.parquet"
    dest.write_bytes(CONTENT)  # already done

    fetch(_entry(src, digest), dest, resume=True)
    assert dest.read_bytes() == CONTENT

    # corrupt it to the same length -> completeness check passes, checksum fails
    dest.write_bytes(b"x" * len(CONTENT))
    with pytest.raises(ChecksumMismatch):
        fetch(_entry(src, digest), dest, resume=True)


def test_no_checksum_skips_verification(tmp_path: Path) -> None:
    src, _ = _source(tmp_path)
    dest = tmp_path / "sample.parquet"
    fetch(_entry(src, None), dest)
    assert dest.read_bytes() == CONTENT
