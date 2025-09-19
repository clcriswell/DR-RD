"""Utilities for ensuring planner tasks include concrete, actionable detail."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

__all__ = [
    "string_has_concrete_detail",
    "task_contains_concrete_detail",
    "ensure_plan_task_specificity",
]


_STANDARD_PATTERN = re.compile(
    r"\b(?:ISO(?:/IEC)?|IEC|ASTM|IEEE|FDA|CFR|UL|EN|GDPR|HIPAA|SOC\s?2|MIL-STD|NIST|ASHRAE|ANSI|CE|RoHS|REACH|USPTO)"
    r"\s?[A-Z0-9\-:.]*\b",
    re.IGNORECASE,
)

_NUMBER_WITH_UNIT_PATTERN = re.compile(
    r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s?(?:ms|s|sec|seconds|minutes|min|hours|hz|khz|mhz|ghz|bps|kbps|mbps|gbps|tbps|"
    r"ppm|ppb|%|percent|°c|°f|k|kelvin|nm|µm|um|mm|cm|m|km|kg|g|mg|lb|lbs|amp|amps|ma|a|v|kv|w|kw|mw|kwh|db|psi|kpa|mpa|"
    r"bar|joule|rpm|mph|km/h|ft|inch|in|°|samples|units|batches|trials|people|fte|ftes|iteration|iterations|sprints|"
    r"weeks|days|months|quarters|mpa|mpg|gpm|l|ml)\b",
    re.IGNORECASE,
)

_MAGNITUDE_PATTERN = re.compile(
    r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s?(?:million|m|thousand|k|billion|b)\b",
    re.IGNORECASE,
)

_TARGET_PATTERN = re.compile(r"(?:>=|<=|<|>|±|target|threshold|limit|cap|tolerance)", re.IGNORECASE)

_CURRENCY_PATTERN = re.compile(r"\$\s?\d")

_TRL_PATTERN = re.compile(r"\btrl\s*[0-9]\b", re.IGNORECASE)

_PERCENT_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d+)?%")


def string_has_concrete_detail(text: str) -> bool:
    """Return True if the provided string contains measurable detail."""

    if not text:
        return False

    normalized = text.strip()
    if not normalized:
        return False

    if _STANDARD_PATTERN.search(normalized):
        return True
    if _NUMBER_WITH_UNIT_PATTERN.search(normalized):
        return True
    if _MAGNITUDE_PATTERN.search(normalized):
        return True
    if _CURRENCY_PATTERN.search(normalized):
        return True
    if _TRL_PATTERN.search(normalized):
        return True
    if _PERCENT_PATTERN.search(normalized):
        return True

    if any(char.isdigit() for char in normalized):
        if _TARGET_PATTERN.search(normalized):
            return True
        if re.search(r"\b\d+\s?(?:x|×)\b", normalized, re.IGNORECASE):
            return True
        if re.search(r"\b\d{2,}\b", normalized):
            return True

    return False


def _iter_task_strings(task: Mapping[str, Any]) -> Iterable[str]:
    for key in ("title", "summary", "description"):
        value = task.get(key)
        if isinstance(value, str):
            yield value
    for key in ("inputs", "outputs", "constraints"):
        value = task.get(key)
        if isinstance(value, str):
            yield value
        elif isinstance(value, Iterable):
            for item in value:
                if item is None:
                    continue
                text = str(item)
                if text:
                    yield text


def task_contains_concrete_detail(task: Mapping[str, Any]) -> bool:
    """Return True when any planner task field includes actionable specificity."""

    if not isinstance(task, Mapping):
        return False

    return any(string_has_concrete_detail(segment) for segment in _iter_task_strings(task))


_ROLE_DETAIL_LIBRARY: dict[str, tuple[str, ...]] = {
    "cto": (
        "Budget the system control loop latency to ≤ 10 ms end-to-end and reserve ≥ 20% CPU headroom.",
    ),
    "research scientist": (
        "Design experiments collecting ≥ 30 samples and targeting ≥ 95% reproducibility at 20±2 °C.",
    ),
    "regulatory": (
        "Map deliverables to ISO 13485:2016 and FDA 21 CFR 820 checkpoints with documented owners.",
    ),
    "finance": (
        "Model unit economics at a 10,000-unit scale with ±5% variance on gross margin assumptions.",
    ),
    "marketing analyst": (
        "Quantify TAM and SAM across ≥ 2 segments and include a $25M year-3 revenue projection.",
    ),
    "marketing agent": (
        "Run positioning tests with ≥ 100 survey responses and target Net Promoter Score ≥ 60.",
    ),
    "marketing": (
        "Run positioning tests with ≥ 100 survey responses and target Net Promoter Score ≥ 60.",
    ),
    "ip analyst": (
        "Review ≥ 3 prior-art patents across CPC classes and capture publication year and jurisdiction.",
    ),
    "patent": (
        "Draft provisional claim scope referencing USPTO 37 CFR 1.53 rules with ≥ 3 independent claims.",
    ),
    "hrm": (
        "Plan staffing mix to onboard 5 specialized FTE within 45 days including safety training milestones.",
    ),
    "materials engineer": (
        "Select materials meeting ASTM D638 tensile strength ≥ 60 MPa and UL 94 V-0 flammability ratings.",
    ),
    "qa": (
        "Define verification matrix hitting ≥ 90% coverage on safety-critical test cases before release.",
    ),
    "simulation": (
        "Set simulation mesh resolution ≤ 2 mm and solver convergence tolerance ≤ 0.001 for the system model.",
    ),
    "dynamic specialist": (
        "Specify next iteration with KPI uplift target ≥ 15% relative to the current baseline metrics.",
    ),
    "chief scientist": (
        "Advance research roadmap to reach TRL 5 within 2 quarters while maintaining ≥ 80% confidence.",
    ),
    "mechanical systems lead": (
        "Define actuator tolerances within ±0.5 mm and certify load rating ≥ 1.5 kN for critical assemblies.",
    ),
    "default": (
        "State at least one measurable acceptance criterion (e.g., ≥ 90% reliability or completion within 30 days).",
    ),
}


def ensure_plan_task_specificity(plan: MutableMapping[str, Any]) -> bool:
    """Inject quantitative detail into planner tasks lacking specificity."""

    if not isinstance(plan, MutableMapping):
        return False

    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        return False

    changed = False
    role_usage: dict[str, int] = defaultdict(int)

    for task in tasks:
        if not isinstance(task, MutableMapping):
            continue
        if task_contains_concrete_detail(task):
            continue

        role_value = str(task.get("role") or "").strip().lower() or "default"
        hints = _ROLE_DETAIL_LIBRARY.get(role_value) or _ROLE_DETAIL_LIBRARY.get("default")
        if not hints:
            continue

        index = role_usage[role_value] % len(hints)
        role_usage[role_value] += 1
        detail_hint = hints[index]

        constraints = task.get("constraints")
        if isinstance(constraints, list):
            constraint_list = [
                str(item).strip() for item in constraints if str(item).strip()
            ]
        elif isinstance(constraints, str):
            constraint_list = [constraints.strip()] if constraints.strip() else []
        elif constraints is None:
            constraint_list = []
        else:
            text = str(constraints).strip()
            constraint_list = [text] if text else []

        if detail_hint not in constraint_list:
            constraint_list.append(detail_hint)
            changed = True

        task["constraints"] = constraint_list

    return changed

