# Patent Integrations

`dr_rd.integrations.patents` provides light wrappers over public patent search
APIs. The `search_patents(query, caps)` function normalises results to a common
schema:

```json
{
  "source": "patentsview",
  "id": "1234567",
  "title": "Example",
  "abstract": "...",
  "assignee": "Example Corp",
  "inventors": ["A. Smith"],
  "cpc": ["G06F"],
  "pub_date": "2020-01-01",
  "url": "https://patentsview.org/patent/1234567"
}
```

Backends are enabled via `config/apis.yaml` with per-call caps on timeout and
maximum results. Supported backends:

- **PatentsView (USPTO)** – keyless access for basic metadata.
- **EPO OPS** – optional, requires `EPO_OPS_KEY` environment variable.

Tests mock network calls; in production all requests use a tiny helper with
timeouts and retries. Only normalised metadata is returned and stored.
