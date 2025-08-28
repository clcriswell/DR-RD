from __future__ import annotations

import random
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import feature_flags

# Paths
_ROOT = Path(__file__).resolve().parents[2]
_MODELS_CFG_PATH = _ROOT / "config" / "models.yaml"
_BUDGETS_PATH = _ROOT / "config" / "budgets.yaml"

_models_cfg: Dict[str, Any] | None = None
_budgets_cfg: Dict[str, Any] | None = None


def _load_cfg() -> Dict[str, Any]:
    global _models_cfg, _budgets_cfg
    if _models_cfg is None:
        with open(_MODELS_CFG_PATH, "r", encoding="utf-8") as fh:
            _models_cfg = yaml.safe_load(fh) or {}
    if _budgets_cfg is None:
        with open(_BUDGETS_PATH, "r", encoding="utf-8") as fh:
            _budgets_cfg = yaml.safe_load(fh) or {}
    return _models_cfg


@dataclass
class ModelSpec:
    provider: str
    name: str
    purpose: List[str]
    ctx: int
    speed_class: str
    price_in: float
    price_out: float


@dataclass
class RouteContext:
    role: Optional[str]
    purpose: str
    retrieval_policy: Optional[str] = None
    budget_profile: Optional[str] = None
    size_hint: int = 0
    latency_target_ms: Optional[int] = None
    flags: Dict[str, Any] | None = None


@dataclass
class RouteDecision:
    provider: str
    model: str
    reason: str
    backups: List[ModelSpec] = field(default_factory=list)
    gray_probe: bool = False
    budget_est: Dict[str, Any] = field(default_factory=dict)
    slo: Dict[str, Any] = field(default_factory=dict)


def _model_from_id(model_id: str) -> ModelSpec:
    cfg = _load_cfg()
    provider, name = model_id.split("/", 1)
    prov = cfg.get("providers", {}).get(provider, {})
    for m in prov.get("models", []):
        if m.get("name") == name:
            return ModelSpec(
                provider=provider,
                name=name,
                purpose=m.get("purpose", []),
                ctx=int(m.get("ctx", 0)),
                speed_class=m.get("speed_class", ""),
                price_in=float(m.get("price_per_1k_in", 0.0)),
                price_out=float(m.get("price_per_1k_out", 0.0)),
            )
    raise KeyError(f"unknown model {model_id}")


def _provider_models_for_purpose(provider: str, purpose: str) -> List[ModelSpec]:
    cfg = _load_cfg()
    prov = cfg.get("providers", {}).get(provider, {})
    specs: List[ModelSpec] = []
    for m in prov.get("models", []):
        if purpose in m.get("purpose", []):
            specs.append(
                ModelSpec(
                    provider=provider,
                    name=m.get("name"),
                    purpose=m.get("purpose", []),
                    ctx=int(m.get("ctx", 0)),
                    speed_class=m.get("speed_class", ""),
                    price_in=float(m.get("price_per_1k_in", 0.0)),
                    price_out=float(m.get("price_per_1k_out", 0.0)),
                )
            )
    return specs


def list_candidates(purpose: str, role: Optional[str] = None) -> Dict[str, List[str]]:
    cfg = _load_cfg().get("routing", {})
    defaults = cfg.get("defaults", {}).get(purpose, {})
    if role:
        role_cfg = cfg.get("role_overrides", {}).get(role, {})
        defaults = role_cfg.get(purpose, defaults)
    return {
        "preferred": list(defaults.get("preferred", [])),
        "backups": list(defaults.get("backups", [])),
    }


def estimate_tokens(prompt_meta: Optional[Dict[str, Any]] = None) -> int:
    prompt_meta = prompt_meta or {}
    return int(prompt_meta.get("tokens", prompt_meta.get("size_hint", 0)))


def _cost_risk(spec: ModelSpec, tokens: int, ctx: RouteContext) -> bool:
    profile = ctx.budget_profile or feature_flags.BUDGET_PROFILE
    budget = _budgets_cfg.get(profile, {}).get(ctx.purpose, {}) if _budgets_cfg else {}
    max_tokens = int(budget.get("max_tokens", 0))
    if max_tokens and tokens > max_tokens:
        return True
    return False


def choose_model(ctx: RouteContext) -> RouteDecision:
    cfg = _load_cfg()
    routing = list_candidates(ctx.purpose, ctx.role)
    preferred_specs = [_model_from_id(mid) for mid in routing.get("preferred", [])]
    backup_specs = [_model_from_id(mid) for mid in routing.get("backups", [])]

    est_tokens = ctx.size_hint
    preferred_specs = [m for m in preferred_specs if m.ctx >= est_tokens]
    backup_specs = [m for m in backup_specs if m.ctx >= est_tokens]

    if not preferred_specs and backup_specs:
        chosen = backup_specs.pop(0)
        reason = "no_preferred_ctx"
    else:
        chosen = preferred_specs[0]
        reason = "preferred"
        backup_specs = preferred_specs[1:] + backup_specs

    if _cost_risk(chosen, est_tokens, ctx):
        cheaper = sorted(
            _provider_models_for_purpose(chosen.provider, ctx.purpose),
            key=lambda m: m.price_in,
        )[0]
        if cheaper.name != chosen.name:
            backup_specs.insert(0, chosen)
            chosen = cheaper
            reason = "budget_downshift"

    gray_ratio = cfg.get("slos", {}).get("gray_routing_ratio", 0.0)
    gray_probe = False
    if backup_specs and random.random() < gray_ratio:
        gray_probe = True
        chosen, backup_specs = backup_specs[0], [chosen] + backup_specs[1:]
        reason = "gray_probe"

    slo = {
        "target_ms": cfg.get("slos", {}).get("target_latency_ms", {}).get(ctx.purpose),
        "max_ms": cfg.get("slos", {}).get("max_latency_ms", {}).get(ctx.purpose),
    }

    return RouteDecision(
        provider=chosen.provider,
        model=chosen.name,
        reason=reason,
        backups=backup_specs,
        gray_probe=gray_probe,
        budget_est={"est_tokens": est_tokens},
        slo=slo,
    )


def failover_policy(decision: RouteDecision) -> RouteDecision | None:
    if not decision.backups:
        return None
    nxt = decision.backups[0]
    remaining = decision.backups[1:]
    return RouteDecision(
        provider=nxt.provider,
        model=nxt.name,
        reason="failover",
        backups=remaining,
        gray_probe=False,
        budget_est=decision.budget_est,
        slo=decision.slo,
    )


__all__ = [
    "ModelSpec",
    "RouteContext",
    "RouteDecision",
    "list_candidates",
    "estimate_tokens",
    "choose_model",
    "failover_policy",
]
