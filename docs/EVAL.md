# Evaluation Harness

This harness runs **golden tasks** end-to-end through the same orchestrator used by the UI, scores the outputs, and builds a scoreboard.

## Datasets
- Place datasets under `eval/datasets/`.
- JSONL format is preferred; CSV files are auto-mapped.
- Each line represents one task with fields:
```json
{
  "id": "t001",
  "idea": "Summarize the DR RD pipeline in 5 bullets.",
  "mode": "standard",
  "limits": {"budget_usd": 0.10, "max_tokens": 2000},
  "expected_keywords": ["planner", "executor"],
  "forbidden_keywords": ["password"],
  "min_words": 40,
  "max_words": 200,
  "tags": ["smoke"],
  "seed": 42
}
```
Unknown top‑level keys are ignored.

## Running
### Streamlit page
Use **Evaluation** page to pick a dataset, optionally enable *Use LLM rubric*, and run. Results are saved under `.dr_rd/eval/{timestamp}`.

### CLI
```
python scripts/eval_run.py --dataset eval/datasets/default.jsonl
```
Additional flags: `--use-llm`, `--concurrency N`, `--out DIR`.
The command exits 0 only if all items succeed and pass‑rate ≥ 0.7.

## Scores
- **heuristic** – keyword coverage with penalties for forbidden terms, out-of-bounds length, or errors.
- **llm** – optional rubric score from `utils.llm_client`.
- **final** – average of heuristic and llm when available.

Scoreboard files:
- `scoreboard.csv` – raw table.
- `scoreboard.md` – table plus highlights and aggregates.

## Determinism & Cost
- Use `seed` in datasets for reproducible runs.
- Adjust provider/model or budget limits to control spend.

Artifacts live under `.dr_rd/eval/{timestamp}/`.
