# AI R&D Center (Streamlit)

[![Build CI](https://github.com/clcriswell/DR-RD/actions/workflows/ci.yml/badge.svg)](https://github.com/clcriswell/DR-RD/actions/workflows/ci.yml)
[![Tests](https://github.com/clcriswell/DR-RD/actions/workflows/test.yml/badge.svg)](https://github.com/clcriswell/DR-RD/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-unknown-lightgrey.svg)](docs/BADGES.md#coverage)
[![License](https://img.shields.io/github/license/clcriswell/DR-RD)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-46A2F1.svg)](https://github.com/astral-sh/ruff)

A public Streamlit application that masks a user’s idea, decomposes it into
multi-disciplinary research tasks, and orchestrates AI agents to synthesize a
prototype or development plan.

See the docs index in [docs/INDEX.md](docs/INDEX.md) for more information.
New contributors should start with the [Migration Guide](docs/MIGRATION_GUIDE_v1_to_v2.md).

_Current repo state_
**Step 1:** Minimal Streamlit front-end + “Creation Planner” prompt.

The planner now uses OpenAI's JSON mode for reliable parsing.

## Quick start (local)

```bash
git clone https://github.com/YOUR_USERNAME/rnd_tool.git
cd rnd_tool
python -m venv .venv && source .venv/bin/activate   # PowerShell: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```
