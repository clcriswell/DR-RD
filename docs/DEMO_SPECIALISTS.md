# Specialist Demo

This repository ships a minimal demo that exercises the Materials, QA, and Finance Specialist agents along with the ad‑hoc Dynamic Agent.

## Running

### Streamlit UI

```bash
streamlit run app.py
```

Use the **Specialists** panel to select agents, provide a task title/description and JSON inputs, then click **Run Selected Specialists**. The **Dynamic Agent (ad hoc)** expander accepts a JSON spec describing a temporary role.

### Script

```bash
python scripts/demo_specialists.py
```

The script invokes Materials, QA, and Finance Specialist agents with retrieval disabled, then repeats the Materials call with retrieval enabled to demonstrate citations. Outputs are printed to stdout.

## Expected Keys

- **Materials:** `role`, `task`, `summary`, `properties`, `tradeoffs`, `risks`, `next_steps`, `sources`
- **QA:** `role`, `task`, `requirements_matrix`, `coverage`, `defect_stats`, `risks`, `next_steps`, `sources`
- **Finance Specialist:** `role`, `task`, `unit_economics`, `npv`, `simulations`, `assumptions`, `risks`, `next_steps`, `sources`
- **Dynamic Agent:** `role`, `task`, `result`, `sources`

## Flags & Logs

Feature flags in the sidebar (or passed via `flag_overrides`) control retrieval, evaluation, and provenance capture. Provenance logs default to the `runs/` directory and can be inspected via the **Agent Trace** panel or by reading the `provenance.jsonl` files directly.
