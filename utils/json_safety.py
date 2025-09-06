import json
import logging
import re

log = logging.getLogger(__name__)

CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
UNQUOTED_KEY_RE = re.compile(r"([,{]\s*)([A-Za-z0-9_]+)\s*:")
MISSING_VALUE_RE = re.compile(r":\s*(?=[,}])")
TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def strip_fences(txt: str) -> str:
    return re.sub(CODE_FENCE_RE, "", txt or "").strip()


def extract_braced(txt: str) -> str:
    # Take largest {...} block to avoid pre/post chatter
    s = txt.find("{")
    e = txt.rfind("}")
    return txt[s : e + 1] if s != -1 and e != -1 and e > s else txt


def light_sanitize(txt: str) -> str:
    # Remove trailing commas before } or ]
    txt = re.sub(r",\s*([}\]])", r"\1", txt)
    # Replace smart quotes
    txt = txt.replace("“", '"').replace("”", '"').replace("’", "'")
    return txt


def auto_repair_json(txt: str) -> str:
    """Attempt lightweight structural fixes for common JSON issues."""
    if not isinstance(txt, str):
        return txt
    txt = TRAILING_COMMA_RE.sub(r"\1", txt)
    txt = UNQUOTED_KEY_RE.sub(lambda m: f'{m.group(1)}"{m.group(2)}":', txt)
    txt = MISSING_VALUE_RE.sub(": null", txt)
    return txt


def parse_json_loose(raw: str):
    """Attempt multiple strategies to coerce LLM text into JSON."""
    if raw is None:
        raise ValueError("No planner text to parse")
    candidates = []
    candidates.append(strip_fences(raw))
    candidates.append(extract_braced(candidates[0]))
    candidates.append(light_sanitize(candidates[-1]))
    last_err = None
    for c in candidates:
        try:
            return json.loads(c)
        except Exception as e:
            last_err = e
            # Try auto-repair on the candidate before moving on
            try:
                return json.loads(auto_repair_json(c))
            except Exception as e2:  # pragma: no cover - best effort
                last_err = e2
                continue
    log.warning("Planner JSON repair engaged. head=%r", (raw or "")[:120])
    # Final recovery: find first '{'..matching '}' chunk-by-chunk
    candidate = extract_braced(raw)
    try:
        while candidate.count("{") > candidate.count("}"):
            candidate += "}"
        return json.loads(candidate)
    except Exception:
        last_comma = candidate.rfind(",")
        if last_comma == -1:
            raise ValueError("Planner JSON parse failed") from last_err
        candidate = candidate[:last_comma] + "}"
        return json.loads(candidate)
