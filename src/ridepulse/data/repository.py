"""Repository seam over the processed-parquet store.

Consumers ask for a dataset by *logical name* and never construct paths
themselves (spec §8, Repository pattern). Swapping the storage layout means
changing only ``_REGISTRY``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_REGISTRY: dict[str, str] = {
    "cleaned_trips": "processed/cleaned_trips.parquet",
    "demand_features": "processed/demand_features.parquet",
    "eta_features": "processed/eta_features.parquet",
}


class ParquetRepository:
    """Read/write the pipeline's processed tables by logical name."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path(self, name: str) -> Path:
        """Resolved path for ``name``; raise :class:`KeyError` if unknown."""
        try:
            rel = _REGISTRY[name]
        except KeyError:
            known = ", ".join(sorted(_REGISTRY))
            raise KeyError(f"unknown dataset {name!r}; known: {known}") from None
        return self.root / rel

    def exists(self, name: str) -> bool:
        return self.path(name).exists()

    def write(self, name: str, df: pd.DataFrame) -> Path:
        p = self.path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p, index=False)
        return p

    def read(self, name: str) -> pd.DataFrame:
        p = self.path(name)
        if not p.exists():
            raise FileNotFoundError(f"{name!r} not built yet: {p}")
        return pd.read_parquet(p)

    @staticmethod
    def datasets() -> list[str]:
        return sorted(_REGISTRY)
