#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" -q
.venv/bin/pytest -q
.venv/bin/python -m tiny_tool_agent --mock "What is 17 * 24?"
echo smoke ok
