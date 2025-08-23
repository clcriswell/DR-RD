#!/usr/bin/env python3
"""Generate repo_map.yaml and docs/REPO_MAP.md from repository state."""
from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "repo_map.yaml"
DOC_PATH = ROOT / "docs" / "REPO_MAP.md"
TEMPLATE_PATH = ROOT / "docs" / "templates" / "repo_map.md.j2"


def _git_sha() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    )


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def _get_runtime_modes():
    return _load_yaml(ROOT / "config" / "modes.yaml")


def _get_agent_registry() -> dict[str, str]:
    content = (ROOT / "core" / "agents_registry.py").read_text()
    imports = re.findall(
        r"from core\.agents\.([a-zA-Z0-9_]+)_agent import ([A-Za-z0-9_]+)", content
    )
    class_to_module = {cls: f"core/agents/{name}_agent.py" for name, cls in imports}
    mapping: dict[str, str] = {}
    entries = re.findall(r"\"([^\"]+)\":\s*([A-Za-z0-9_]+)\(", content)
    for role, cls in entries:
        module_path = class_to_module.get(cls)
        if module_path:
            mapping[role] = module_path
    return mapping


def build_repo_map() -> dict:
    git_sha = _git_sha()
    modes = _get_runtime_modes()
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
        "architecture": "Planner → Router/Registry → Executor → Synthesizer",
        "runtime_modes": modes,
        "env_flags": [
            "DRRD_MODE",
            "RAG_ENABLED",
            "ENABLE_LIVE_SEARCH",
            "SERPAPI_KEY",
        ],
        "modules": modules,
        "agent_registry": agent_registry,
        "config_files": [
            {"path": "config/modes.yaml", "required_keys": ["test", "deep"]},
            {"path": "config/prices.yaml", "required_keys": ["models"]},
        ],
        "prompts_dir": "prompts",
        "tests_dir": "tests",
        "orchestrators_dir": "orchestrators",
        "ui_files": ["app.py", "app/__init__.py"],
        "execution_flow": "User idea → Planner → Router/Registry → Executor → Synthesizer → UI",
        "rules_ref": "docs/REPO_RULES.md",
    }
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
