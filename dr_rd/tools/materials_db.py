"""Simple in-repo materials database lookup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

_SAMPLE_DATA = [
    {
        "name": "Aluminum",
        "property": "tensile_strength",
        "value": 310,
        "units": "MPa",
        "source": "sample",
    },
    {
        "name": "Steel",
        "property": "tensile_strength",
        "value": 400,
        "units": "MPa",
        "source": "sample",
    },
    {
        "name": "Polycarbonate",
        "property": "modulus",
        "value": 2.3,
        "units": "GPa",
        "source": "sample",
    },
]


@dataclass
class MaterialsDBAdapter:
    """Interface for materials database adapters."""

    def lookup(self, query: str) -> List[Dict]:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryMaterialsAdapter(MaterialsDBAdapter):
    """In-memory adapter backed by a small sample dataset."""

    def __init__(self, data: List[Dict] | None = None) -> None:
        self.data = data or list(_SAMPLE_DATA)

    def lookup(self, query: str) -> List[Dict]:
        q = query.lower()
        return [r for r in self.data if q in r["name"].lower() or q in r["property"].lower()]


_adapter: MaterialsDBAdapter = InMemoryMaterialsAdapter()


def lookup_materials(query: str) -> List[Dict]:
    """Lookup materials by name or property."""
    return _adapter.lookup(query)
