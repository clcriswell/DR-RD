from __future__ import annotations

from pathlib import Path

from .fs_utils import bundle_complete


def _parse_gs_uri(uri: str) -> tuple[str, str]:
    rem = uri[5:] if uri.startswith("gs://") else uri
    bucket, _, prefix = rem.partition("/")
    return bucket, prefix


def ensure_local_faiss_bundle(cfg: dict, logger) -> dict:
    """Ensure a FAISS bundle exists locally, optionally downloading from GCS."""
    local_dir = Path(cfg.get("faiss_index_local_dir") or ".faiss_index")
    local_dir.mkdir(parents=True, exist_ok=True)
    if bundle_complete(local_dir):
        return {"present": True, "path": str(local_dir), "source": "local"}
    mode = str(cfg.get("faiss_bootstrap_mode", "download"))
    uri = cfg.get("faiss_index_uri")
    if mode != "download" or not uri or not str(uri).startswith("gs://"):
        reason = "bootstrap_skipped" if mode != "download" else "no_uri"
        return {"present": False, "path": str(local_dir), "source": "none", "reason": reason}
    bucket, prefix = _parse_gs_uri(str(uri))
    files = 0
    total = 0
    try:
        from google.cloud import storage  # type: ignore

        client = storage.Client()
        blobs = list(client.list_blobs(bucket, prefix=prefix))
        for blob in blobs:
            rel = blob.name[len(prefix) :].lstrip("/")
            dest = local_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(dest)
            files += 1
            total += getattr(blob, "size", 0) or 0
        ok = bundle_complete(local_dir)
        logger.info(
            "FAISSBootstrap bucket=%s prefix=%s files=%d bytes=%d result=%s reason=%s",
            bucket,
            prefix,
            files,
            total,
            "ok" if ok else "fail",
            "" if ok else "incomplete",
        )
        if ok:
            return {"present": True, "path": str(local_dir), "source": "gcs"}
        return {"present": False, "path": str(local_dir), "source": "none", "reason": "incomplete"}
    except Exception as e:  # pragma: no cover - network failures
        msg = str(e)
        logger.warning(
            "FAISSBootstrap bucket=%s prefix=%s files=%d bytes=%d result=fail reason=%s",
            bucket,
            prefix,
            files,
            total,
            msg,
        )
        return {"present": False, "path": str(local_dir), "source": "none", "reason": msg}
