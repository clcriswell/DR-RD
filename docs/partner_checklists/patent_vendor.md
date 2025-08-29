# Patent Vendor Checklist

- **API/Schema Contract**: verify endpoints and JSON schema for patent search results.
- **Auth/Keys/Env Names**: `PATENT_VENDOR_KEY` in environment.
- **QoS/Rate-Limit**: document per-minute and daily limits; implement retry/backoff.
- **Cost Budget**: set maximum spend and alerts.
- **PII/Privacy**: ensure patent data caching policy and redaction rules.
- **Test Fixtures**: include mocked patent responses for CI.
- **Acceptance**: run integration tests against staging endpoint.
