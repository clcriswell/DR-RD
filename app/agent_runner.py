# Command-line runner for DR-RD agents with Firestore caching.
from __future__ import annotations

import argparse
import hashlib
from typing import Optional

from core import cache

from core.model_router import pick_model, CallHints
from core.llm_client import call_openai
import logging

_DEF_PROMPTS = {
    "Low": "Provide a brief high-level summary.",
    "Medium": "Provide a balanced level of technical detail.",
    "High": "Provide exhaustive technical depth with all relevant details.",
}


def run_agent(role: str, prompt: str, depth: str = "Low") -> str:
    """Run an agent for ``role`` with ``prompt`` and ``design depth``.

    The result is cached in Firestore keyed by a SHA1 hash of the inputs.
    """
    depth_norm = depth.capitalize()
    task_hash = hashlib.sha1(f"{role}|{prompt}|{depth_norm}".encode()).hexdigest()

    cached = cache.get_result(task_hash)
    if cached:
        return cached

    depth_suffix = _DEF_PROMPTS.get(depth_norm, _DEF_PROMPTS["Low"])
    message = f"{prompt}\n\n{depth_suffix}"

    sel = pick_model(CallHints(stage="exec"))
    logging.info(f"Model[exec]={sel['model']} params={sel['params']}")
    result = call_openai(
        model=sel["model"],
        messages=[
            {"role": "system", "content": f"You are acting as {role}."},
            {"role": "user", "content": message},
        ],
        **sel["params"],
    )["text"]
    result = (result or "").strip()
    cache.save_result(task_hash, result)
    return result


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single DR-RD agent")
    parser.add_argument("role", help="Agent role to execute")
    parser.add_argument("prompt", help="Prompt/task for the agent")
    parser.add_argument(
        "--design_depth",
        default="low",
        choices=["low", "medium", "high"],
        help="Desired design depth for the response",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = _parse_args(argv)
    depth = args.design_depth.capitalize()
    output = run_agent(args.role, args.prompt, depth)
    print(output)


if __name__ == "__main__":  # pragma: no cover
    main()
