from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Protocol


class Hook(Protocol):
    def on_iteration(self, state: Dict[str, Any]) -> None: ...
    def on_complete(
        self, metrics: Dict[str, Any], outputs_dir: Path | None
    ) -> None: ...
    def on_failure(self, metrics: Dict[str, Any], outputs_dir: Path | None) -> None: ...
