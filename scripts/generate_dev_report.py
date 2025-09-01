"""Generate a PDF report summarizing recent development steps.

This script demonstrates a simple planning/execution loop and
produces a PDF report containing the steps and recent commit history.
It uses the :func:`core.reporting.pdf.to_pdf` utility which falls back to
a minimal PDF implementation if ReportLab is unavailable.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from core.reporting import pdf


def main() -> None:
    """Run a planning loop and export the results to a PDF report."""
    tasks = [
        {"stage": "Planning", "detail": "Gather requirements and outline tasks."},
        {"stage": "Execution", "detail": "Implement features and fix bugs."},
        {"stage": "Testing", "detail": "Run unit tests and lint checks."},
        {"stage": "Reporting", "detail": "Generate development summary PDF."},
    ]

    lines = []
    for step in tasks:  # planning/execution loop
        lines.append(f"{step['stage']}: {step['detail']}")

    try:
        commits = subprocess.check_output(
            ["git", "log", "--oneline", "-n", "5"], text=True
        )
        lines.append("\nRecent commits:\n" + commits.strip())
    except Exception:  # pragma: no cover - git may be unavailable
        lines.append("\nRecent commits: (unavailable)")

    report_text = "\n".join(lines)

    out_dir = Path("reports/build")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "development_report.pdf"
    info = pdf.to_pdf(report_text, str(out_file))
    print(f"Wrote {info['bytes']} bytes to {info['path']}")


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
