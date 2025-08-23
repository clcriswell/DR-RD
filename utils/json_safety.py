import json
import logging
import re

log = logging.getLogger(__name__)

CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


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
