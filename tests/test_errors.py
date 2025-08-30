import json
import os

from utils.errors import (
    SafeError,
    as_json,
    classify,
    make_safe_error,
    redact,
)


class APIError(Exception):
    pass


class TimeoutCustomError(Exception):
    pass


class ValidationIssue(ValueError):
    pass


class DiskFailure(IOError):
    pass


def test_classify_and_support_id():
    run_id = "run123"
    err = make_safe_error(APIError("bad request"), run_id=run_id, phase="plan", step_id=None)
    assert err.kind == "api"
    assert err.support_id and len(err.support_id) == 8

    err = make_safe_error(TimeoutCustomError("waiting"), run_id=run_id, phase="exec", step_id=None)
    assert err.kind == "timeout"

    err = make_safe_error(ValidationIssue("oops"), run_id=run_id, phase="exec", step_id=None)
    assert err.kind == "validation"

    err = make_safe_error(DiskFailure("disk"), run_id=run_id, phase="exec", step_id=None)
    assert err.kind == "io"


def test_redact_tokens_and_roundtrip():
    home = os.path.expanduser("~")
    text = f"api_key=sk-1234567890abcdef Bearer abcdefg123 test@example.com {home}/file.txt"
    redacted = redact(text)
    assert "sk-123" not in redacted
    assert "Bearer abcdefg123" not in redacted
    assert "test@example.com" not in redacted
    assert home not in redacted

    safe = SafeError(
        kind="api",
        user_message="u",
        tech_message="t",
        traceback=None,
        support_id="abcdef12",
        context={"run_id": "r1"},
    )
    blob = as_json(safe)
    data = json.loads(blob.decode("utf-8"))
    assert data["kind"] == "api"
    assert data["support_id"] == "abcdef12"

