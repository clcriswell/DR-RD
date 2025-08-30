from io import BytesIO
from zipfile import ZipFile

from utils.bundle import build_zip_bundle


def _fake_read(run_id: str, name: str, ext: str) -> bytes:
    return f"{name}.{ext}".encode()


def _fake_list(run_id: str):
    return [("extra", "txt")]


def test_build_zip_bundle():
    data = build_zip_bundle(
        "r1",
        [],
        read_bytes=_fake_read,
        list_existing=_fake_list,
        sanitize=lambda n, e, b: b,
    )
    with ZipFile(BytesIO(data)) as zf:
        names = sorted(zf.namelist())
        contents = {n: zf.read(n) for n in names}
    assert names == ["extra.txt", "report.md", "summary.csv", "trace.json"]
    assert contents["trace.json"] == b"trace.json"
    assert contents["extra.txt"] == b"extra.txt"
