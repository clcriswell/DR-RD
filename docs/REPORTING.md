# Reporting & Provenance

Agent outputs may include citations like `[S1]` referring to retrieved
sources.  The final synthesised report appends a **References** section that
lists each source in order and links to the original URL or document title.

The Streamlit UI exposes export buttons under the *Exports* tab:

- **Download Sources (JSONL):** writes `audits/<project>/sources.jsonl` using
  `core.retrieval.provenance.export_jsonl`.
- **Download Final Report (Markdown):** saves the current report with the
  rendered reference list.

These exports enable external auditing of both tool usage and information
provenance.
