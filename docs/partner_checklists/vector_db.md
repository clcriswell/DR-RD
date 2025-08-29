# Vector DB Checklist

- **API/Schema Contract**: confirm indexing and query schema.
- **Auth/Keys/Env Names**: `VECTOR_DB_API_KEY` in environment.
- **QoS/Rate-Limit**: document indexing throughput and query latency budgets.
- **Cost Budget**: configure TTL and cache size to control spend.
- **PII/Privacy**: ensure encrypted storage and explicit TTL settings.
- **Test Fixtures**: include sample embeddings and query cases.
- **Acceptance**: validate privacy filters and result accuracy.
