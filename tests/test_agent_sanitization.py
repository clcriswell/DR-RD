import jsonschema

from core.agents.prompt_agent import coerce_types, strip_additional_properties


def test_sanitization_coerces_and_strips():
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "findings": {"type": "string"},
        },
        "required": ["summary", "findings"],
        "additionalProperties": False,
    }
    payload = {"summary": ["a", "b"], "findings": ["x", "y"], "image_query": "img"}
    coerced = coerce_types(payload, schema)
    cleaned = strip_additional_properties(coerced, schema)
    jsonschema.validate(cleaned, schema)
    assert cleaned == {"summary": "a; b", "findings": "x; y"}
