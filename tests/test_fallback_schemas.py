import json
import jsonschema
import pytest

SCHEMAS = [
    "dr_rd/schemas/cto_v2_fallback.json",
    "dr_rd/schemas/regulatory_v2_fallback.json",
    "dr_rd/schemas/marketing_v2_fallback.json",
]


@pytest.mark.parametrize("path", SCHEMAS)
def test_minimal_payload_valid(path):
    with open(path, encoding="utf-8") as fh:
        schema = json.load(fh)
    payload = {"role": "r", "task": "t", "summary": "s"}
    jsonschema.validate(payload, schema)
