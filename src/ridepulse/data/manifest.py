"""Download manifest: the checksummed list of source files the pipeline needs.

The manifest is a YAML list of entries::

    - name: yellow_tripdata_2023-01
      url: https://.../yellow_tripdata_2023-01.parquet
      sha256: null            # filled in after the first verified download
      kind: parquet

``sha256`` may be ``null`` before the first download; once filled, every later
fetch is checksum-verified against it (see :mod:`ridepulse.data.download`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, TypeAdapter

Kind = Literal["parquet", "csv", "zip"]


class ManifestEntry(BaseModel):
    """One source file."""

    model_config = {"frozen": True, "extra": "forbid"}

    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    sha256: str | None = None
    kind: Kind


_ENTRY_LIST = TypeAdapter(list[ManifestEntry])


class Manifest(BaseModel):
    """A parsed, validated manifest."""

    model_config = {"frozen": True}

    entries: list[ManifestEntry]

    def entry(self, name: str) -> ManifestEntry:
        """Return the entry named ``name`` or raise :class:`KeyError`."""
        for e in self.entries:
            if e.name == name:
                return e
        raise KeyError(f"no manifest entry named {name!r}")

    def names(self) -> list[str]:
        return [e.name for e in self.entries]


def load_manifest(path: str | Path) -> Manifest:
    """Parse and validate the YAML manifest at ``path``.

    Raises :class:`pydantic.ValidationError` if any entry is missing a required
    field or has an unknown ``kind``.
    """
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, list):
        raise ValueError(
            f"manifest must be a YAML list of entries, got {type(raw).__name__}"
        )
    entries = _ENTRY_LIST.validate_python(raw)
    return Manifest(entries=entries)
