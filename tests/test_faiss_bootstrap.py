import sys
import types
from pathlib import Path

from dr_rd.knowledge.bootstrap import ensure_local_faiss_bundle


def _install_fake_storage(client):
    mod = types.SimpleNamespace(Client=lambda *a, **k: client)
    cloud = types.SimpleNamespace(storage=mod)
    sys.modules.setdefault("google", types.SimpleNamespace())
    sys.modules["google"].cloud = cloud
    sys.modules["google.cloud"] = cloud
    sys.modules["google.cloud.storage"] = mod


def test_local_present(tmp_path):
    local = tmp_path / "idx"
    local.mkdir()
    (local / "index.faiss").write_text("x")
    (local / "texts.json").write_text("{}")
    cfg = {"faiss_index_local_dir": str(local)}
    logger = types.SimpleNamespace(
        info=lambda *a, **k: None, warning=lambda *a, **k: None
    )
    res = ensure_local_faiss_bundle(cfg, logger)
    assert res["present"] and res["source"] == "local"


def test_download_success(tmp_path):
    class FakeBlob:
        def __init__(self, name):
            self.name = name
            self.size = 1

        def download_to_filename(self, path):
            Path(path).write_text("x")

    class FakeClient:
        def list_blobs(self, bucket, prefix=None):
            return [
                FakeBlob(f"{prefix}/index.faiss"),
                FakeBlob(f"{prefix}/texts.json"),
            ]

    _install_fake_storage(FakeClient())
    cfg = {
        "faiss_index_local_dir": str(tmp_path / "idx"),
        "faiss_index_uri": "gs://bkt/prefix",
    }
    logger = types.SimpleNamespace(
        info=lambda *a, **k: None, warning=lambda *a, **k: None
    )
    res = ensure_local_faiss_bundle(cfg, logger)
    assert res["present"] and res["source"] == "gcs"


def test_download_missing_bucket(tmp_path):
    class FakeClient:
        def list_blobs(self, bucket, prefix=None):
            raise FileNotFoundError("missing")

    _install_fake_storage(FakeClient())
    cfg = {
        "faiss_index_local_dir": str(tmp_path / "idx"),
        "faiss_index_uri": "gs://bkt/prefix",
    }
    logs: list = []
    logger = types.SimpleNamespace(
        info=lambda *a, **k: None, warning=lambda *args, **k: logs.append(args)
    )
    res = ensure_local_faiss_bundle(cfg, logger)
    assert not res["present"] and res["source"] == "none"
    assert "missing" in (res.get("reason") or "")
    assert logs
