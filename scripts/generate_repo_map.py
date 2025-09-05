#!/usr/bin/env python3
"""Generate repo_map.yaml and docs/REPO_MAP.md from repository state."""
from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
YAML_PATH = ROOT / "repo_map.yaml"
DOC_PATH = ROOT / "docs" / "REPO_MAP.md"
TEMPLATE_PATH = ROOT / "docs" / "templates" / "repo_map.md.j2"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def _get_runtime_modes():
    modes = _load_yaml(ROOT / "config" / "modes.yaml") or {}
    aliases = [m for m in ("test", "deep") if m in modes]
    return {"standard": modes.get("standard", {})}, aliases


def _get_agent_registry() -> dict[str, str]:
    import inspect
    import sys
    import types

    if "streamlit" not in sys.modules:
        def _cr(func=None, *a, **k):
            if func:
                return func
            return lambda f: f
        sys.modules["streamlit"] = types.SimpleNamespace(cache_resource=_cr)
    if "openai" not in sys.modules:

        class _Resp:
            def create(self, *a, **k):
                pass

        class _OpenAI:
            def __init__(self, *a, **k):
                self.responses = _Resp()

        openai_stub = types.SimpleNamespace(APIStatusError=Exception, OpenAI=_OpenAI)
        sys.modules["openai"] = openai_stub
    if "httpx" not in sys.modules:
        sys.modules["httpx"] = types.SimpleNamespace()
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace()
    if "pydantic" not in sys.modules:

        class _BaseModel:
            pass

        def Field(*a, **k):
            return None

        pydantic_stub = types.SimpleNamespace(BaseModel=_BaseModel, Field=Field)
        sys.modules["pydantic"] = pydantic_stub
    if "PIL" not in sys.modules:
        sys.modules["PIL"] = types.SimpleNamespace(Image=object)
    if "google" not in sys.modules:
        google = types.SimpleNamespace()
        google.cloud = types.SimpleNamespace(storage=types.SimpleNamespace())
        sys.modules["google"] = google
        sys.modules["google.cloud"] = google.cloud
        sys.modules["google.cloud.storage"] = google.cloud.storage
    from core.agents import unified_registry

    mapping: dict[str, str] = {}
    for role, cls in unified_registry.AGENT_REGISTRY.items():
        path = Path(inspect.getsourcefile(cls)).resolve().relative_to(ROOT)
        mapping[role] = path.as_posix()
    return mapping


def build_repo_map() -> dict:
    git_sha = _git_sha()
    modes, aliases = _get_runtime_modes()
    agent_registry = _get_agent_registry()
    modules = []
    for role, module in agent_registry.items():
        modules.append(
            {
                "path": module,
                "role": f"Agent[{role}]",
                "responsibilities": [],
                "inputs": [],
                "outputs": [],
                "invoked_by": [],
                "invokes": [],
            }
        )
    for path in (ROOT / "orchestrators").glob("*.py"):
        modules.append(
            {
                "path": f"orchestrators/{path.name}",
                "role": "Orchestrator",
                "responsibilities": [],
                "inputs": [],
                "outputs": [],
                "invoked_by": [],
                "invokes": [],
            }
        )
    for path in (ROOT / "core" / "summarization").glob("*.py"):
        modules.append(
            {
                "path": f"core/summarization/{path.name}",
                "role": "Summarization",
                "responsibilities": [],
                "inputs": [],
                "outputs": [],
                "invoked_by": [],
                "invokes": [],
            }
        )
    for path in ["app.py", "app/__init__.py"]:
        modules.append(
            {
                "path": path,
                "role": "UI",
                "responsibilities": [],
                "inputs": [],
                "outputs": [],
                "invoked_by": [],
                "invokes": [],
            }
        )

    data = {
        "version": 1,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "git_sha": git_sha,
        "entry_points": [
            {"name": "streamlit_app", "path": "app.py"},
            {"name": "package_init", "path": "app/__init__.py:main"},
        ],
        "architecture": "Planner → Router/Registry → Executor → Summarization → Synthesizer",
        "runtime_modes": modes,
        "env_flags": [
            "RAG_ENABLED",
            "ENABLE_LIVE_SEARCH",
            "EVALUATORS_ENABLED",
            "PARALLEL_EXEC_ENABLED",
            "SERPAPI_KEY",
        ],
        "modules": modules,
        "agent_registry": agent_registry,
        "config_files": [
            {"path": "config/modes.yaml", "required_keys": ["standard"]},
            {"path": "config/prices.yaml", "required_keys": ["models"]},
        ],
        "prompts_dir": "prompts",
        "tests_dir": "tests",
        "orchestrators_dir": "orchestrators",
        "ui_files": ["app.py", "app/__init__.py"],
        "execution_flow": (
            "User idea → Planner → Router/Registry → Executor → " "Summarization → Synthesizer → UI"
        ),
        "rules_ref": "docs/REPO_RULES.md",
    }
    if aliases:
        data["mode_aliases"] = aliases
    return data


def render_repo_map_doc(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_PATH.parent)))
    template = env.get_template(TEMPLATE_PATH.name)
    return template.render(**data)


def main() -> None:
    data = build_repo_map()
    YAML_PATH.write_text(yaml.safe_dump(data, sort_keys=False))
    DOC_PATH.write_text(render_repo_map_doc(data))
    print(f"Wrote {YAML_PATH} and {DOC_PATH}")


if __name__ == "__main__":
    main()
