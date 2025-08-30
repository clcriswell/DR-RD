# Privacy and Data Controls

DR-RD stores limited data under the `.dr_rd/` directory in your user home.
This includes telemetry event logs, optional survey responses, consent state
and run artifacts. The application provides controls to manage this data.

## Consent

On first launch you are asked whether to allow anonymous telemetry and
optional in-app surveys. Your choice is stored in `.dr_rd/consent.json` and
can be changed at any time from the **Privacy & Data** page.

Consent options:

- **Telemetry** – operational metrics that help improve the app.
- **Surveys** – occasional satisfaction questions after runs.

Declining either feature disables associated logging and prompts.

## Retention

Telemetry files and run directories are retained for a limited number of
days. Defaults are 30 days for events and 60 days for run artifacts. These
limits can be adjusted on the **Privacy & Data** page. From the same page you
can purge telemetry files or runs older than the configured window.

Command line purging is also available:

```bash
python scripts/telemetry_purge.py --older-than 30
```

## Delete or Export Run Data

Use the **Privacy & Data** page to delete all data for a specific run or to
remove only its telemetry events. To export a run with associated telemetry,
run:

```bash
python scripts/privacy_export.py --run-id <RUN_ID> --out <DEST_DIR>
```

## Stored Files

```
.dr_rd/
  consent.json          # telemetry and survey consent
  config.json           # user preferences including retention windows
  telemetry/            # event logs and survey responses
  runs/                 # run artifacts
```

Removing the `.dr_rd/` directory will reset the application to a clean state
but permanently deletes any run data and logs.

