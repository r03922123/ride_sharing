"""Checksum-verified, resumable file download.

Supports ``file://`` (used in tests) and ``http(s)://`` URLs. A failed checksum
raises loudly — there is no silent skip (spec §10).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

from ridepulse.data.manifest import ManifestEntry

_CHUNK = 1 << 20  # 1 MiB


class ChecksumMismatch(RuntimeError):
    """Raised when a downloaded file's SHA-256 does not match the manifest."""


def sha256_of(path: str | Path) -> str:
    """Return the hex SHA-256 digest of the file at ``path``."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(path: str | Path, sha256: str) -> None:
    """Raise :class:`ChecksumMismatch` if ``path`` does not hash to ``sha256``."""
    actual = sha256_of(path)
    if actual.lower() != sha256.lower():
        raise ChecksumMismatch(
            f"{path}: expected sha256 {sha256}, got {actual}"
        )


def _local_path(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if parsed.scheme == "":
        return Path(url)
    return None


def _remote_size(url: str) -> int | None:
    local = _local_path(url)
    if local is not None:
        return local.stat().st_size if local.exists() else None
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req) as resp:  # noqa: S310 - trusted manifest URLs
            length = resp.headers.get("Content-Length")
            return int(length) if length is not None else None
    except Exception:
        return None


def _copy_from(start: int, src: Path, dest: Path) -> None:
    mode = "ab" if start > 0 else "wb"
    with open(src, "rb") as sfh, open(dest, mode) as dfh:
        sfh.seek(start)
        shutil.copyfileobj(sfh, dfh, _CHUNK)


def _http_download(start: int, url: str, dest: Path) -> None:
    req = urllib.request.Request(url)
    if start > 0:
        req.add_header("Range", f"bytes={start}-")
    mode = "ab" if start > 0 else "wb"
    with urllib.request.urlopen(req) as resp, open(dest, mode) as dfh:  # noqa: S310
        # If the server ignored the Range request, restart from scratch.
        if start > 0 and resp.status != 206:
            dfh.close()
            dest.write_bytes(b"")
            with urllib.request.urlopen(url) as full, open(dest, "wb") as fresh:  # noqa: S310
                shutil.copyfileobj(full, fresh, _CHUNK)
            return
        shutil.copyfileobj(resp, dfh, _CHUNK)


def fetch(entry: ManifestEntry, dest: str | Path, *, resume: bool = True) -> Path:
    """Download ``entry.url`` to ``dest``, resuming a partial file if possible.

    After the transfer, if ``entry.sha256`` is set, the file is checksum-verified
    and :class:`ChecksumMismatch` is raised on any difference.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    total = _remote_size(entry.url)
    have = dest.stat().st_size if dest.exists() else 0

    if have and total is not None and have == total:
        start = -1  # already complete
    elif resume and have and total is not None and have < total:
        start = have
    else:
        start = 0
        if dest.exists():
            dest.unlink()

    if start >= 0:
        local = _local_path(entry.url)
        if local is not None:
            _copy_from(start, local, dest)
        else:
            _http_download(start, entry.url, dest)

    if entry.sha256:
        verify_checksum(dest, entry.sha256)
    return dest


def fetch_all(
    entries: list[ManifestEntry], dest_dir: str | Path, *, resume: bool = True
) -> dict[str, Path]:
    """Fetch every entry into ``dest_dir``; return ``name -> path``."""
    dest_dir = Path(dest_dir)
    out: dict[str, Path] = {}
    for e in entries:
        suffix = {"parquet": ".parquet", "csv": ".csv", "zip": ".zip"}[e.kind]
        out[e.name] = fetch(e, dest_dir / f"{e.name}{suffix}", resume=resume)
    return out


def computed_checksums(paths: dict[str, Path]) -> dict[str, str]:
    """Return ``name -> sha256`` for a set of downloaded files."""
    return {name: sha256_of(p) for name, p in paths.items() if os.path.exists(p)}
