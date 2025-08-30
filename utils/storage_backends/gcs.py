from __future__ import annotations

"""GCS storage backend."""

from datetime import timedelta
from typing import Iterable, Optional

try:
    from google.cloud import storage as gcs  # type: ignore
except Exception:  # pragma: no cover - optional
    gcs = None

from ..storage import ObjRef, Storage
from .. import telemetry, secrets


class GCSStorage(Storage):
    backend = "gcs"

    def __init__(self, conf: dict | None = None) -> None:
        if gcs is None:  # pragma: no cover - optional
            raise RuntimeError("google-cloud-storage not installed")
        conf = conf or {}
        self.bucket_name = conf.get("bucket") or secrets.get("GCS_BUCKET") or ""
        self.prefix = conf.get("prefix", "dr_rd")
        self.ttl = int(conf.get("signed_url_ttl_sec", 600))
        if secrets.get("GCP_SERVICE_ACCOUNT"):
            self.client = gcs.Client.from_service_account_info(secrets.get("GCP_SERVICE_ACCOUNT"))  # type: ignore
        else:
            self.client = gcs.Client()  # type: ignore
        self.bucket = self.client.bucket(self.bucket_name)  # type: ignore

    def _blob(self, key: str):
        name = f"{self.prefix}/{key}" if self.prefix else key
        return self.bucket.blob(name)

    def write_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> ObjRef:
        blob = self._blob(key)
        blob.upload_from_string(data, content_type=content_type)
        telemetry.storage_write(self.backend, key, len(data))
        return ObjRef(key=key, size=len(data))

    def read_bytes(self, key: str) -> bytes:
        blob = self._blob(key)
        data = blob.download_as_bytes()
        telemetry.storage_read(self.backend, key, len(data))
        return data

    def exists(self, key: str) -> bool:
        return self._blob(key).exists()

    def list(self, prefix: str) -> Iterable[ObjRef]:
        path = f"{self.prefix}/{prefix}" if self.prefix else prefix
        for blob in self.client.list_blobs(self.bucket_name, prefix=path):  # type: ignore
            key = blob.name[len(self.prefix) + 1 :] if self.prefix else blob.name
            yield ObjRef(key=key, size=blob.size)

    def delete(self, key: str) -> None:
        try:
            self._blob(key).delete()
        except Exception:
            pass

    def url_for(self, key: str, ttl_sec: int) -> Optional[str]:
        try:
            blob = self._blob(key)
            return blob.generate_signed_url(expiration=timedelta(seconds=ttl_sec))  # type: ignore
        except Exception:  # pragma: no cover - best effort
            return None
