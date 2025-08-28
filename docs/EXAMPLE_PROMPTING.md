# Example Prompting

Few-shot examples come from the Example Bank and knowledge base. Candidates are scored for quality, recency and lexical match while enforcing diversity. Safety filters drop items containing PII, secrets or disallowed content and redact unknown links.

When `EXAMPLES_ENABLED=true` and a prompt template defines an `example_policy`, the `PromptFactory` injects provider-formatted examples. Packs respect provider rules (OpenAI, Anthropic, Gemini) and the global token budget `EXAMPLE_MAX_TOKENS`. Trimmed examples are surfaced under a `few_shots` field with a summary of count and token estimate. Roles can opt out by omitting `example_policy`.
