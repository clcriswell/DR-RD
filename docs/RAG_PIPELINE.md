# Retrieval Pipeline

The retrieval subsystem resolves external context for agents.

1. **Retrievers** – lexical (BM25Lite), dense, knowledge base and optional web search.
2. **Quality scoring** – combines domain reputation, recency and basic heuristics.
3. **Hybrid fusion** – normalises component scores and performs weighted ranking.
4. **Budget clipping** – respects per document and total token budgets from `config/rag.yaml` and router governance.
5. **Bundling** – assigns stable citation markers `[S1]..[Sn]` and returns a `ContextBundle` with `sources`.
6. **Safety** – blocked domains are removed and risky text is redacted.

Agents request retrieval via the `PromptFactory` by specifying a policy (`NONE|LIGHT|AGGRESSIVE`). The factory emits a `retrieval_plan` consumed by the executor which calls `core.retrieval.run_retrieval` and injects clipped evidence before model invocation.
