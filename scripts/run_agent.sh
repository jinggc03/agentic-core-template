#!/bin/bash
# Run agent standalone (CLI mode)

cd "$(dirname "$0")/.."
python -m app.agents.cli
