from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, Iterable, List, Sequence, Tuple, Union, Any
import random

ValueOptions = Union[Sequence[Any], Tuple[float, float]]


@dataclass
class DesignSpace:
    """Simple schema describing bounds or options for design parameters.

    Parameters are provided as a mapping from parameter name to either:
    - a sequence of discrete options
    - a tuple ``(low, high)`` representing a continuous range sampled uniformly
    """

    space: Dict[str, ValueOptions]

    def iter_grid(self) -> Iterable[Dict[str, Any]]:
        """Iterate over all combinations in the discrete design space.

        All parameters must have discrete option lists for grid search.
        """
        keys: List[str] = list(self.space.keys())
        option_lists: List[Sequence[Any]] = []
        for key, opts in self.space.items():
            if isinstance(opts, tuple):
                raise ValueError("Grid search requires discrete option lists")
            option_lists.append(list(opts))
        for values in product(*option_lists):
            yield dict(zip(keys, values))

    def sample(self) -> Dict[str, Any]:
        """Sample a single design from the space."""
        design: Dict[str, Any] = {}
        for key, opts in self.space.items():
            if isinstance(opts, tuple):
                design[key] = random.uniform(opts[0], opts[1])
            else:
                design[key] = random.choice(list(opts))
        return design

    def summarize(self, design: Dict[str, Any], limit: int = 3) -> str:
        """Return a concise string summary of ``design`` parameters.

        Only the first ``limit`` parameters are included to keep logs brief.
        """
        parts: List[str] = []
        for key in self.space.keys():
            if key in design:
                parts.append(f"{key}={design[key]}")
                if len(parts) >= limit:
                    break
        return ", ".join(parts)
