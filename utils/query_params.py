import base64
import json
from typing import Any, Dict, List, Tuple
from urllib.parse import quote, unquote

SHORTEN_IDEA = 200


def _b64_json(d: dict) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(d, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")


def _b64_json_load(s: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(s.encode("ascii")).decode("utf-8"))


def encode_config(cfg: dict) -> Dict[str, str]:
    # cfg conforms to RunConfig adapter dict
    qp: Dict[str, str] = {}
    if (idea := cfg.get("idea")):
        qp["idea"] = idea[:SHORTEN_IDEA]
    if (mode := cfg.get("mode")):
        qp["mode"] = str(mode)
    if (b := cfg.get("budget_limit_usd")) is not None:
        qp["budget"] = str(b)
    if (mx := cfg.get("max_tokens")) is not None:
        qp["max"] = str(mx)
    if (src := cfg.get("knowledge_sources")):
        qp["src"] = ",".join(src)
    if (adv := cfg.get("advanced")):
        qp["adv"] = _b64_json(adv)
    return qp


def decode_config(params: Dict[str, str]) -> dict:
    cfg: Dict[str, Any] = {}
    if "idea" in params:
        cfg["idea"] = params["idea"]
    if "mode" in params:
        cfg["mode"] = params["mode"]
    if "budget" in params:
        try:
            cfg["budget_limit_usd"] = float(params["budget"])
        except Exception:
            pass
    if "max" in params:
        try:
            cfg["max_tokens"] = int(params["max"])
        except Exception:
            pass
    if "src" in params:
        cfg["knowledge_sources"] = [s for s in params["src"].split(",") if s]
    if "adv" in params:
        try:
            cfg["advanced"] = _b64_json_load(params["adv"])
        except Exception:
            cfg["advanced"] = {}
    return cfg


def merge_into_defaults(defaults: dict, decoded: dict) -> dict:
    out = defaults.copy()
    out.update({k: v for k, v in decoded.items() if v is not None})
    return out


def view_state_from_params(params: Dict[str, str]) -> dict:
    return {
        "view": params.get("view") or "run",
        "trace_view": params.get("trace_view") or "summary",
        "trace_query": params.get("q") or "",
        "run_id": params.get("run_id") or None,
    }


# loop guard keys for st.session_state
QP_APPLIED_KEY = "_qp_applied"
