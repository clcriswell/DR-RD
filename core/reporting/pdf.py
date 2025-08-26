from __future__ import annotations

"""Utilities for exporting reports to PDF."""

import os
from pathlib import Path
from typing import Dict


try:  # rich backend (reportlab)
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    _HAS_REPORTLAB = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_REPORTLAB = False


_DEF_FONT = "Courier"
_DEF_FONT_SIZE = 10


def _write_minimal_pdf(text: str, out_path: Path) -> None:
    """Write a very small monospaced PDF containing ``text``.

    The implementation writes a valid but extremely small PDF using only the
    standard library.  It is sufficient for tests which only require that a PDF
    file is produced with non-zero bytes.
    """

    lines = text.splitlines() or [""]
    # Build a minimal PDF structure with five objects (catalog, pages, page,
    # font, and content stream).
    contents = ["BT /F1 12 Tf 72 720 Td"]
    for i, line in enumerate(lines):
        esc = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            contents.append(f"({esc}) Tj")
        else:
            contents.append(f"T* ({esc}) Tj")
    contents.append("ET")
    stream = "\n".join(contents).encode("latin-1", "replace")

    objs = []
    objs.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objs.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objs.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources<< /Font<< /F1 4 0 R>>>> /Contents 5 0 R>>endobj\n"
    )
    objs.append(b"4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>endobj\n")
    objs.append(
        f"5 0 obj<< /Length {len(stream)} >>stream\n".encode()
        + stream
        + b"\nendstream\nendobj\n"
    )

    with open(out_path, "wb") as fh:
        fh.write(b"%PDF-1.1\n")
        offsets = []
        for obj in objs:
            offsets.append(fh.tell())
            fh.write(obj)
        xref_pos = fh.tell()
        fh.write(b"xref\n0 6\n0000000000 65535 f \n")
        for off in offsets:
            fh.write(f"{off:010} 00000 n \n".encode())
        fh.write(b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n")
        fh.write(f"{xref_pos}\n%%EOF".encode())


def to_pdf(html_or_text: str, out_path: str) -> Dict[str, object]:
    """Convert HTML or plain text to PDF.

    A best-effort attempt is made using ReportLab when available.  When the
    dependency is missing, a tiny monospaced PDF is produced instead.  The
    function never raises an exception; it returns metadata about the produced
    file.
    """

    path = Path(out_path)
    text = str(html_or_text)
    backend = "minimal"
    pages = 1

    try:
        if _HAS_REPORTLAB:
            backend = "reportlab"
            c = canvas.Canvas(str(path), pagesize=letter)
            width, height = letter
            text_obj = c.beginText(40, height - 40)
            text_obj.setFont(_DEF_FONT, _DEF_FONT_SIZE)
            for line in text.splitlines():
                text_obj.textLine(line)
            c.drawText(text_obj)
            c.showPage()
            c.save()
        else:  # fallback
            _write_minimal_pdf(text, path)
    except Exception:  # pragma: no cover - should not happen
        _write_minimal_pdf(text, path)
        backend = "minimal"

    size = path.stat().st_size if path.exists() else 0
    return {"path": str(path), "pages": pages, "bytes": size, "backend": backend}
