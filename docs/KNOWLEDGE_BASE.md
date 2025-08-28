# Knowledge Base

The knowledge base persists agent outputs and their source citations. Records are stored as JSONL files under `.dr_rd/kb/` with the schema described in `dr_rd/kb/models.py`. A lightweight index (`kb_index.jsonl`) is rebuilt during nightly distillation.

Query the store using `dr_rd.kb.store.query()` and compact it with `store.compact()`. Each `KBRecord` includes provenance span identifiers for privacy review. Data lives on the local filesystem by default and should be handled carefully when sharing artifacts.
