from google.cloud import storage


def _client():
    """Return a storage client using default credentials."""
    return storage.Client()


def upload_bytes_to_gcs(data: bytes, filename: str, content_type: str, bucket_name: str, prefix: str = "rd_results/") -> str:
    """Upload data to a GCS bucket and return the public URL."""
    bkt = _client().bucket(bucket_name)
    blob = bkt.blob(prefix + filename)
    blob.upload_from_string(data, content_type=content_type)
    return f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
