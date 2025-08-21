import importlib.util
import json
import os
import fitz
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


def test_generate_pdf_wraps_long_lines(tmp_path):
    if not md_spec:
        pytest.skip("markdown_pdf not installed")
    long_value = " ".join(["x" * 20] * 15)
    json_text = json.dumps({"key": long_value}, indent=2)
    md = f"```json\n{json_text}\n```"
    pdf_bytes = generate_pdf(md)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_text = "".join(page.get_text() for page in doc).replace("\n", "")
    doc.close()
    assert long_value[:40] in page_text
    assert long_value[-40:] in page_text
    (tmp_path / "json_report.pdf").write_bytes(pdf_bytes)


def test_generate_pdf_normalizes_heading_levels(tmp_path):
    if not md_spec:
        pytest.skip("markdown_pdf not installed")
    md = "## Subtitle\n\nContent\n\n### Subsection"
    pdf_bytes = generate_pdf(md)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    toc = doc.get_toc()
    doc.close()
    assert toc and toc[0][0] == 1
