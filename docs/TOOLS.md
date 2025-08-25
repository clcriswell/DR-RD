# Tools

This repository exposes three pluggable tools used by agents.

## Code I/O
- **read_repo(globs: list[str]) -> list[dict]**: return `[{path, text}]` for matching files.
- **plan_patch(diff_spec: str) -> str**: pass-through diff preview.
- **apply_patch(diff: str, dry_run: bool = True) -> dict**: validate or apply unified diffs.

Guardrails:
- Access limited to repository root.
- Only text files with extensions: `.py`, `.md`, `.txt`, `.yaml`, `.yml`, `.json`, `.toml`, `.cfg`.
- Denylist patterns from `config/secret_paths.yaml` plus common binaries.

Caps (from `config/tools.yaml`): `max_files`, runtime, token budget.

## Digital Twin Simulation
- **simulate(params: dict) -> dict**
  - Single run: inputs.
  - Parameter sweep: `{"sweep": [inputs...]}`
  - Monte Carlo: `{"monte_carlo": int, "seed": optional}` with `mean_output` summary.

Backend is lightweight and pluggable.

## Vision
- **analyze_image(file_or_bytes, tasks) -> dict** where tasks ⊆ `{ocr, classify, detect}`.
- **analyze_video(file_path: str, sample_rate_fps: int, tasks) -> dict**.

Dependencies (Pillow, OpenCV, pytesseract) are optional; functions degrade gracefully.

## Tool Router & Provenance
`core/tool_router.py` registers tools and enforces config caps.
Each call logs provenance: `{agent, tool, inputs_hash, outputs_digest, tokens, wall_time}`.
Retrieve logs with `get_provenance()`.
