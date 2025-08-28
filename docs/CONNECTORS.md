# Connectors

This project ships lightweight connectors for public patent and regulatory APIs.
All connectors read API keys from the environment and honour simple rate limits
and on-disk caching.

| Connector | Env Keys | Endpoints |
| --- | --- | --- |
| USPTO PatentsView | `USPTO_API_KEY` | search, fetch by publication/application |
| EPO OPS | `EPO_OPS_KEY` | search, fetch (stub) |
| Regulations.gov | `REG_GOV_API_KEY` | search documents, fetch document |
| GovInfo CFR | `GOVINFO_API_KEY` | lookup CFR text by title/part/section |
| FDA Devices | `FDA_API_KEY` | 510(k)/device search |

## Usage

Each connector exposes pure functions returning normalised JSON records. All
network requests pass through `connectors.commons.http_json` which includes
retry with exponential backoff, optional request signing and a simple rate limit
guard.

Responses are cached via a TTL file cache located under `DRRD_CACHE_DIR`
(default `.cache`).

Example:

```python
from dr_rd.connectors.uspto_patents import search_patents

res = search_patents("battery cooling")
print(res["items"][0]["title"])
```
