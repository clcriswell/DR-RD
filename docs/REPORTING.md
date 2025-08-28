# Reporting

Reports are composed from planner specs, agent outputs and synthesizer summaries. The canonical schema lives in `dr_rd/reporting/schemas/report_v1.json`. `dr_rd.reporting.compose()` builds a strict JSON structure and exporters render Markdown and HTML.

Use `scripts/build_report.py --plan plan.json --agents agents.jsonl --synth synth.json --out out_dir` to generate artifacts.
\n## Where it fits\n\nPlanner → Router → Executor → Synthesizer → KB & Reports completes the loop for durable artifacts.
