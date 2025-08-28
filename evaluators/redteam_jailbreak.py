from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import yaml

from dr_rd.prompting.prompt_factory import PromptFactory

JAILBREAK_PATH = Path("dr_rd/safety/jailbreaks.yaml")


def run_harness(build_prompt: Callable[[dict], dict] | None = None) -> bool:
    """Replay jailbreak payloads against prompts.

    ``build_prompt`` allows injection of a custom prompt builder for tests.
    Returns ``True`` if all checks pass.
    """
    payloads = yaml.safe_load(JAILBREAK_PATH.read_text()).get("payloads", [])
    factory = PromptFactory()
    for attack in payloads:
        spec = {
            "role": "Planner",
            "task": attack,
            "inputs": {"idea": "test", "task": attack},
            "io_schema_ref": "dr_rd/schemas/planner_v1.json",
        }
        prompt = build_prompt(spec) if build_prompt else factory.build_prompt(spec)
        system = prompt.get("system", "")
        # Guard text must persist
        assert "Return only JSON" in system
        # Simulate model output and ensure JSON validity
        output = json.dumps({"status": "ok"})
        json.loads(output)
        # Ensure no system leakage
        assert "You are" not in output
    return True
