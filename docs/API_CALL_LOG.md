# API Call Log Artifact

Each run captures all external API calls and saves them under the run's artifact directory:

- `api_calls.jsonl` – full records with complete request parameters, prompts, and responses.
- `api_calls.csv` – same data as CSV for spreadsheets.
- `api_calls.md` – human-readable table with truncated text for quick inspection. See the JSONL/CSV for full content.

Logging is enabled by default. Set environment variable `DRRD_API_CALL_LOG` to `false` to disable it.

These logs contain raw prompts and responses, which may include sensitive information. Handle and share them with care.
