from __future__ import annotations

"""S3 storage backend (thin wrapper around boto3)."""

from typing import Iterable, Optional

try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover - optional
    boto3 = None

from ..storage import ObjRef, Storage
from .. import telemetry
from .. import secrets


class S3Storage(Storage):
    backend = "s3"

    def __init__(self, conf: dict | None = None) -> None:
        if boto3 is None:  # pragma: no cover - optional
            raise RuntimeError("boto3 not installed")
        conf = conf or {}
        self.bucket = conf.get("bucket") or secrets.get("S3_BUCKET") or ""
        self.prefix = conf.get("prefix", "dr_rd")
        self.ttl = int(conf.get("signed_url_ttl_sec", 600))
        session = boto3.session.Session(
            aws_access_key_id=secrets.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secrets.get("AWS_SECRET_ACCESS_KEY"),
            region_name=secrets.get("AWS_REGION"),
        )
        endpoint = secrets.get("S3_ENDPOINT_URL")
        self.client = session.client("s3", endpoint_url=endpoint)  # type: ignore

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    def write_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> ObjRef:
        fk = self._full_key(key)
        self.client.put_object(Bucket=self.bucket, Key=fk, Body=data, ContentType=content_type)  # type: ignore
        telemetry.storage_write(self.backend, key, len(data))
        return ObjRef(key=key, size=len(data))

    def read_bytes(self, key: str) -> bytes:
        fk = self._full_key(key)
        resp = self.client.get_object(Bucket=self.bucket, Key=fk)  # type: ignore
        data = resp["Body"].read()
        telemetry.storage_read(self.backend, key, len(data))
        return data

    def exists(self, key: str) -> bool:
        fk = self._full_key(key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=fk)  # type: ignore
            return True
        except Exception:
            return False

    def list(self, prefix: str) -> Iterable[ObjRef]:
        fk = self._full_key(prefix)
        paginator = self.client.get_paginator("list_objects_v2")  # type: ignore
        for page in paginator.paginate(Bucket=self.bucket, Prefix=fk):
            for obj in page.get("Contents", []):
                key = obj["Key"][len(self.prefix) + 1 :] if self.prefix else obj["Key"]
                yield ObjRef(key=key, size=obj.get("Size"))

    def delete(self, key: str) -> None:
        fk = self._full_key(key)
        self.client.delete_object(Bucket=self.bucket, Key=fk)  # type: ignore

    def url_for(self, key: str, ttl_sec: int) -> Optional[str]:
        fk = self._full_key(key)
        try:
            return self.client.generate_presigned_url(  # type: ignore
                "get_object",
                Params={"Bucket": self.bucket, "Key": fk},
                ExpiresIn=ttl_sec,
            )
        except Exception:  # pragma: no cover - best effort
            return None
