from core.reporting import pdf


def test_pdf_fallback(tmp_path, monkeypatch):
    # Simulate missing rich backend
    monkeypatch.setattr(pdf, "_HAS_REPORTLAB", False)
    out = tmp_path / "out.pdf"
    info = pdf.to_pdf("hello", str(out))
    assert out.exists()
    assert info["bytes"] > 0
    assert info["backend"] == "minimal"
