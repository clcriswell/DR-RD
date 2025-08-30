import os
import base64
import json
import json
import json
import pytest

from utils.share_links import sign, verify


def setup_module(module):
    import os
    os.environ["SHARE_SECRET"] = "secret"


def test_round_trip():
    tok = sign("run1", scopes=["trace", "reports"], ttl_sec=60)
    obj = verify(tok)
    assert obj["rid"] == "run1"
    assert "trace" in obj["scopes"]


def test_tampered_payload_fails():
    import base64, json
    tok = sign("run1", scopes=["trace"], ttl_sec=60)
    body, sig = tok.split(".", 1)
    data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    data["rid"] = "other"
    tampered_body = base64.urlsafe_b64encode(
        json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    tampered = tampered_body + "." + sig
    with pytest.raises(ValueError):
        verify(tampered)


def test_expired_token_fails():
    tok = sign("run1", scopes=["trace"], ttl_sec=-1)
    with pytest.raises(ValueError):
        verify(tok)


def test_scope_filter():
    tok = sign("run1", scopes=["trace", "bad"], ttl_sec=60)
    obj = verify(tok)
    assert obj["scopes"] == ["trace"]
