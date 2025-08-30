from __future__ import annotations

import math
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .prefs import load_prefs
from .redaction import redact_text


_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?i)\b(ignore|override|bypass)\b.*\b(instructions|system|guardrails)\b"),
    re.compile(r"(?i)\bprint the system prompt\b"),
    re.compile(r"(?i)\bcopy.*secrets?\b"),
]

_EXFIL_PATTERNS = [
    re.compile(r"/etc/passwd"),
    re.compile(r"C:\\Windows"),
    re.compile(r"(?i)upload to|send to|pastebin|gist"),
    re.compile(r"(?i)http[s]?://"),
    re.compile(r"(?i)password|api[_-]?key"),
]

_PII_PATTERNS = [re.compile(p) for p in [
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b\+?\d[\d \-()]{7,}\d\b",
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b(?:\d[ -]*?){13,19}\b",
]]

_OUTPUT_PATTERNS = [
    re.compile(r"(?i)(;\s*rm -rf|drop table|<script|\$\{\{)")
]


@dataclass(frozen=True)
class SafetyFinding:
    category: str
    severity: str
    span: Tuple[int, int]
    message: str


@dataclass(frozen=True)
class SafetyResult:
    findings: List[SafetyFinding]
    blocked: bool
    score: float


@dataclass(frozen=True)
class SafetyConfig:
    mode: str
    use_llm: bool
    block_categories: List[str]
    high_severity_threshold: float


def _scan_patterns(text: str, patterns: List[re.Pattern[str]], category: str) -> List[SafetyFinding]:
    findings: List[SafetyFinding] = []
    for rx in patterns:
        for m in rx.finditer(text):
            findings.append(
                SafetyFinding(
                    category=category,
                    severity="high" if category in {"exfil", "malicious_instruction", "unsafe_output"} else "med",
                    span=(m.start(), m.end()),
                    message=rx.pattern,
                )
            )
    return findings


def check_text(text: str) -> SafetyResult:
    txt = text or ""
    findings: List[SafetyFinding] = []
    findings += _scan_patterns(txt, _PROMPT_INJECTION_PATTERNS, "prompt_injection")
    findings += _scan_patterns(txt, _EXFIL_PATTERNS, "exfil")
    findings += _scan_patterns(txt, _PII_PATTERNS, "pii")
    findings += _scan_patterns(txt, _OUTPUT_PATTERNS, "unsafe_output")
    blocked = any(f.severity == "high" for f in findings)
    score = min(1.0, len(findings) / 5) if findings else 0.0
    return SafetyResult(findings=findings, blocked=blocked, score=score)


def check_artifact(name: str, text: str) -> SafetyResult:
    return check_text(text)


def merge_results(*results: SafetyResult) -> SafetyResult:
    findings: List[SafetyFinding] = []
    blocked = False
    score = 0.0
    for r in results:
        findings.extend(r.findings)
        blocked = blocked or r.blocked
        score = max(score, r.score)
    return SafetyResult(findings=findings, blocked=blocked, score=score)


def sanitize_text(text: str) -> str:
    s = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub("[\u200B-\u200D\uFEFF]", "", s)
    return redact_text(s)


def llm_advisor(text: str, *, mode: str, budget_ms: int = 800) -> SafetyResult:
    start = time.time()
    try:
        if os.environ.get("NO_NET") == "1":
            return SafetyResult([], False, 0.0)
        prefs = load_prefs()
        if not prefs.get("privacy", {}).get("telemetry_enabled", True):
            return SafetyResult([], False, 0.0)
        from . import llm_client

        prompt = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a safety auditor. Respond with JSON {score:0..1, categories:[]}.",
                },
                {"role": "user", "content": text},
            ],
            "max_tokens": 200,
        }
        remaining = max(0, budget_ms - int((time.time() - start) * 1000))
        if remaining <= 0:
            return SafetyResult([], False, 0.0)
        resp = llm_client.chat(prompt, mode=mode)
        content = ""
        try:
            content = resp["choices"][0]["message"]["content"]
        except Exception:
            content = str(resp)
        data = {}  # type: ignore[var-annotated]
        try:
            data = json.loads(content)
        except Exception:
            data = {}
        cats = [str(c) for c in data.get("categories", [])]
        score = float(data.get("score", 0.0))
        findings = [
            SafetyFinding(category=c, severity="med", span=(-1, -1), message="llm") for c in cats
        ]
        return SafetyResult(findings=findings, blocked=score >= 0.9, score=score)
    except Exception:
        return SafetyResult([], False, 0.0)


def default_config() -> SafetyConfig:
    prefs = load_prefs().get("privacy", {})
    mode = str(prefs.get("safety_mode", "warn"))
    use_llm = bool(prefs.get("safety_use_llm", False))
    block_categories = list(prefs.get("safety_block_categories", ["exfil", "malicious_instruction"]))
    try:
        thr = float(prefs.get("safety_high_threshold", 0.8))
    except Exception:
        thr = 0.8
    thr = max(0.0, min(1.0, thr))
    return SafetyConfig(mode=mode, use_llm=use_llm, block_categories=block_categories, high_severity_threshold=thr)


__all__ = [
    "SafetyFinding",
    "SafetyResult",
    "SafetyConfig",
    "check_text",
    "check_artifact",
    "merge_results",
    "sanitize_text",
    "llm_advisor",
    "default_config",
]
