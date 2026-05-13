#!/bin/bash
# Shell wrapper for cron. Activates the venv and runs the scraper.
# Add to crontab: 0 */4 * * * cd /Users/alexdelgado/flight-scraper && bash run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

python run.py "$@"
