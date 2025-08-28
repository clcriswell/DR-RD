# Compliance-Oriented Retrieval

Regulatory and patent research requires strict evidence handling. Retrieval
policies are tuned for compliance tasks:

* **Mandatory citations** – every evidence item must include a stable `source`
  with `id` and `url`.
* **Jurisdiction tagging** – records explicitly state the issuing authority
  (e.g. `US`).
* **Effective dates** – regulatory records surface `effective_date` when
  available.
* **Synthesiser merging** – the Synthesiser deduplicates evidence by source id
  before rendering.

Agents default to conservative retrieval but may upgrade to aggressive mode when
compliance keywords are detected. Cached results are reused when possible to
stay within budget.
