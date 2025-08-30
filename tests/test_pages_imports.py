"""Ensure Streamlit pages import without side effects."""
from pathlib import Path
import importlib.util


def _load(path: Path) -> None:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[arg-type]


def test_pages_import() -> None:
    for page in Path("pages").glob("*.py"):
        _load(page)
