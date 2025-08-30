from utils import upload_scan


def test_allowed_and_pii_detection(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello")
    assert upload_scan.allowed(p)

    binf = tmp_path / "a.bin"
    binf.write_bytes(b"\x00")
    assert not upload_scan.allowed(binf)

    big = tmp_path / "big.txt"
    big.write_text("a" * (upload_scan.MAX_BYTES + 1))
    assert not upload_scan.allowed(big)

    assert upload_scan.detect_pii("email test@example.com")
    assert not upload_scan.detect_pii("no pii here")
