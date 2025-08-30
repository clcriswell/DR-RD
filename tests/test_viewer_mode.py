import os
import pytest

from utils.share_links import sign, viewer_from_query


def setup_module(module):
    import os
    os.environ["SHARE_SECRET"] = "secret"


def test_viewer_from_query_true():
    tok = sign("r1", scopes=["trace"], ttl_sec=60)
    viewer, info = viewer_from_query({"share": tok})
    assert viewer is True
    assert info["rid"] == "r1"


def test_viewer_from_query_expired():
    tok = sign("r1", scopes=["trace"], ttl_sec=-1)
    viewer, info = viewer_from_query({"share": tok})
    assert viewer is False
    assert info["error"] == "exp"
