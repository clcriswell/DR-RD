# Compliance & Citation Layer

The `dr_rd.compliance` package provides simple checklist and citation utilities.
Profiles live under `dr_rd/compliance/profiles/` and define jurisdiction-specific
checklist items. Load a profile with `checker.load_profile(profile_id)` and run a
text against it with `checker.check(text, profile, context)`.

The checker extracts naïve "claims" from the text and determines which checklist
items are satisfied based on the presence of `item.tag` keywords. It returns a
`ComplianceReport` containing coverage, unmet item ids and notes.

`citation.build_citation_graph` pairs claims with retrieval sources and assigns
stable labels `[S1]`, `[S2]` ... . `validate_citations` enforces a domain
allow‑list and minimum coverage fraction (see `config/apis.yaml` under
`CITATIONS`).

The Streamlit UI exposes toggles to enable patent/regulatory APIs and run manual
compliance checks. Reports can be exported as JSON for audit trails.
