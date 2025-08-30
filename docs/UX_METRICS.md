# UX Metrics

## Metrics
- **Task success**: percentage of runs completing without errors.
- **Time on task**: elapsed seconds from `start_run` to export.
- **Error rate**: `error_shown` events divided by `start_run` events.
- **Clicks to complete**: count of button events until export.
- **Engagement signals**: dwell time, tab focus, and scroll depth.
- **SUS**: System Usability Scale responses 0–100.
- **SEQ**: Single Ease Question rating 1–7.
- **CES**: Customer Effort Score rating 1–7.
- **NPS**: Net Promoter Score from 0–10.
- **Cognitive load proxies**: hesitation time and undo frequency.

## Event Schema
```jsonl
{"event":"start_run","fields":["run_id","ts"]}
{"event":"step_completed","fields":["run_id","step","ts"]}
{"event":"error_shown","fields":["run_id","code","ts"]}
{"event":"export_clicked","fields":["run_id","ts"]}
{"event":"trace_filter_changed","fields":["run_id","filter","ts"]}
{"event":"trace_export_clicked","fields":["run_id","ts"]}
{"event":"nav_page_view","fields":["page","ts"]}
{"event":"survey_shown","fields":["survey","ts"]}
{"event":"survey_submitted","fields":["survey","scores","ts"]}
```

### Sample
```jsonl
{"event":"start_run","run_id":"r1","ts":1710000000}
{"event":"step_completed","run_id":"r1","step":"plan","ts":1710000020}
{"event":"error_shown","run_id":"r1","code":"timeout","ts":1710000030}
{"event":"survey_submitted","survey":"sus","scores":85,"ts":1710000040}
```

## Aggregation
```python
import pandas as pd

df = pd.read_json("events.jsonl", lines=True)
success = 1 - len(df[df.event=="error_shown"]) / len(df[df.event=="start_run"])
duration = df[df.event=="export_clicked"].ts.mean() - df[df.event=="start_run"].ts.mean()
error_rate = len(df[df.event=="error_shown"]) / len(df)
weekly_sus = df[df.event=="survey_submitted"].set_index("ts").scores.resample("7D").mean()
```

## Privacy
- No PII captured; run IDs are anonymous.
- Secrets are redacted before logging.
- Users can opt out by setting `DRRD_TELEMETRY_OPTOUT=1`.

## Telemetry schema + rotation + purge
- Events are validated against a versioned schema (`schema_version`), currently `1`. Older records are upcast on read so analytics stay consistent.
- Writers emit JSONL files daily under `.dr_rd/telemetry/` and roll to `events-YYYYMMDD.partN.jsonl` when they exceed ~25MB.
- `scripts/telemetry_purge.py` deletes old files (`--older-than`/`--keep-last-days`) or removes a specific run's events (`--delete-run`). Use `--dry-run` to preview.
- `scripts/telemetry_export.py` exports logs to CSV or Parquet and offers `usage` or `runs` rollups.

### Examples
```bash
python scripts/telemetry_export.py --days 7 --out events.csv
python scripts/telemetry_export.py --from 2025-01-01 --to 2025-01-31 --out events.parquet --rollup usage
python scripts/telemetry_purge.py --older-than 30
python scripts/telemetry_purge.py --delete-run r123
```
