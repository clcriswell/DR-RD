from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Mapping, Sequence, Optional

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

from .redaction import redact_public
from .storage import key_run


BADGE = {"complete": "✅", "error": "⚠️", "running": "⏳"}


def _clean_config(obj: object) -> object:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            lk = k.lower()
            if any(x in lk for x in ("key", "secret", "token")):
                out[k] = "•••"
            elif isinstance(v, (dict, list)):
                out[k] = _clean_config(v)
            elif isinstance(v, str) and len(v) > 1000:
                out[k] = f"<{len(v)} chars>"
            else:
                out[k] = v
        return out
    if isinstance(obj, list):
        return [_clean_config(v) for v in obj]
    return obj


def _red(s: Optional[str]) -> str:
    return redact_public(s or "")


def _read_artifact(path: Path, max_bytes: int) -> Optional[str]:
    try:
        if not path.exists() or path.stat().st_size > max_bytes:
            return None
        text = path.read_text(encoding="utf-8")
        return _red(text)
    except Exception:
        return None


def build_notebook(
    run_id: str,
    meta: Mapping,
    lock: Mapping,
    rows: Sequence[Mapping],
    artifacts: Sequence[tuple[str, str]] | None = None,
    *,
    include_small_artifacts: bool = True,
    max_embed_bytes: int = 200_000,
) -> bytes:
    """Return UTF 8 encoded .ipynb bytes. Do not hit network. Redact secrets."""

    nb = new_notebook()
    nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3"}
    nb["metadata"]["language_info"] = {
        "name": "python",
        "version": platform.python_version(),
    }

    started = meta.get("started_at")
    completed = meta.get("completed_at")
    status = meta.get("status")
    mode = meta.get("mode")
    details = []
    if started is not None:
        details.append(f"started {started}")
    if completed is not None:
        details.append(f"completed {completed}")
    if status:
        details.append(str(status))
    if mode:
        details.append(str(mode))
    title = f"# DR RD Run {run_id}"
    if details:
        title += " (" + ", ".join(details) + ")"
    nb.cells.append(new_markdown_cell(title))

    repro_lines = []
    provider = lock.get("provider") or lock.get("client")
    model = lock.get("model")
    if provider:
        repro_lines.append(f"- Provider: {provider}")
    if model:
        repro_lines.append(f"- Model: {model}")
    budgets = lock.get("budgets")
    if budgets:
        repro_lines.append(f"- Budgets: `{json.dumps(budgets)}`")
    pins = lock.get("prompt_pins")
    if pins:
        repro_lines.append("- Prompt pins:")
        for k, v in pins.items():
            repro_lines.append(f"  - {k}: {v}")
    repro_lines.append("\n_Warning: secrets have been redacted._")
    nb.cells.append(new_markdown_cell("\n".join(repro_lines)))

    clean_lock = _clean_config(lock)
    nb.cells.append(new_code_cell(json.dumps(clean_lock, ensure_ascii=False, indent=2)))

    for row in rows:
        phase = row.get("phase") or "unknown"
        name = row.get("name") or ""
        status = row.get("status") or ""
        dur = row.get("duration_ms")
        badge = BADGE.get(status, status)
        header = f"## [{phase}] {name} {badge}".rstrip()
        if dur is not None:
            header += f" ({dur} ms)"
        nb.cells.append(new_markdown_cell(header))
        prompt = row.get("prompt")
        if prompt:
            nb.cells.append(new_markdown_cell("**Prompt**\n\n" + _red(str(prompt))))
        summary = row.get("summary")
        if summary:
            nb.cells.append(new_markdown_cell("**Output**\n\n" + _red(str(summary))))
        citations = row.get("citations") or []
        if citations:
            lines = ["**Citations**"]
            for c in citations:
                if isinstance(c, Mapping):
                    doc = _red(str(c.get("doc") or c.get("id") or ""))
                    snip = _red(str(c.get("snippet") or c.get("text") or ""))
                    lines.append(f"- {doc}: {snip}")
                else:
                    lines.append(f"- {_red(str(c))}")
            nb.cells.append(new_markdown_cell("\n".join(lines)))

    if artifacts:
        nb.cells.append(new_markdown_cell("## Artifacts"))
        for name, key in artifacts:
            path = Path(key)
            data = _read_artifact(path, max_embed_bytes) if include_small_artifacts else None
            if data is not None:
                ext = path.suffix.lstrip(".")
                nb.cells.append(new_markdown_cell(f"### {name}"))
                nb.cells.append(new_markdown_cell(f"```{ext}\n{data}\n```"))
            else:
                if path.suffix:
                    display = key_run(run_id, path.stem, path.suffix.lstrip("."))
                else:
                    display = key
                nb.cells.append(
                    new_markdown_cell(
                        f"### {name}\nStored as `{display}`. Fetch via the app."
                    )
                )

    tokens = sum(int(row.get("tokens") or 0) for row in rows)
    cost = sum(float(row.get("cost") or 0.0) for row in rows)
    duration = sum(int(row.get("duration_ms") or 0) for row in rows)
    nb.cells.append(
        new_markdown_cell(
            f"**Totals**\n\n- Tokens: {tokens}\n- Cost: ${cost:.4f}\n- Duration: {duration} ms"
        )
    )

    return nbformat.writes(nb).encode("utf-8")

