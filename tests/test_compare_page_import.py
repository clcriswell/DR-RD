import importlib.util
from pathlib import Path


def test_import_page():
    path = Path("pages/25_Compare.py")
    spec = importlib.util.spec_from_file_location("compare_page", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
