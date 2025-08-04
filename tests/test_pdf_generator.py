import importlib.util
import os
import pytest
from app import generate_pdf

md_spec = importlib.util.find_spec("markdown_pdf")
pytestmark = pytest.mark.skipif(md_spec is None, reason="markdown_pdf not installed")

if md_spec:
    from markdown_pdf import MarkdownPdf


def test_generate_pdf_smoke(monkeypatch, tmp_path):
    if md_spec:
        if not hasattr(MarkdownPdf, "export"):
            def fake_export(self):
                path = tmp_path / "tmp.pdf"
                self.save(path)
                return path.read_bytes()
            monkeypatch.setattr(MarkdownPdf, "export", fake_export, raising=False)
    md = "# Title\n\n- Item 1\n- Item 2\n\n![alt](https://example.com/image.png)"
    pdf_bytes = generate_pdf(md)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 1000
    (tmp_path / "test_report.pdf").write_bytes(pdf_bytes)
