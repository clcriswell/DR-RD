import importlib.util
from pathlib import Path


def test_import_graph_page():
    path = Path("pages/13_Graph.py")
    spec = importlib.util.spec_from_file_location("graph_page", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
