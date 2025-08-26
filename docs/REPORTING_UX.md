# Reporting UX

Reports provide a consolidated view of a run. The reporting pipeline lives in
`core/reporting/` and can export Markdown, HTML and PDF files.

## Sections
Sections rendered by `core.reporting.builder.build_report`:
- Title & cover information
- Executive Summary
- Plan & Tasks
- Key Findings per role/task
- Risks & Next Steps
- Simulations
- Compliance
- References using stable `[S#]` identifiers
- Appendix with tool and cost stats

Sections can be toggled in the UI. All content is passed through the central
redactor (`utils.redaction`) to avoid leaking secrets.

## Export Formats
- **Markdown**: raw text
- **HTML**: bundled with minimal CSS assets
- **PDF**: generated via `core.reporting.pdf.to_pdf`

Exports are capped by `REPORT_MAX_BYTES` and `PDF_MAX_PAGES` from
`config/ui.yaml`. When limits are exceeded the UI surfaces a clear error.
