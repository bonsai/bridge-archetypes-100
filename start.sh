#!/usr/bin/env bash
# agentshell-compatible entrypoint for bridge100
# Usage: hermes run ./start.sh [--mode backend|frontend|record]

set -euo pipefail

MODE="${1:-dev}"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_DIR

case "$MODE" in
  dev|backend)
    echo "Starting FastAPI backend..."
    cd "$REPO_DIR"
    python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    ;;
  frontend)
    echo "Frontend is served at http://localhost:8000/static/ (embedded in FastAPI)"
    ;;
  record)
    echo "Running auto-record pipeline..."
    python3 "$REPO_DIR/scripts/auto_record.py"
    ;;
  nix)
    if command -v nix &>/dev/null; then
      nix develop
    else
      echo "nix not available, running in local python env"
      python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
    fi
    ;;
  *)
    echo "Usage: $0 [dev|backend|frontend|record|nix]"
    exit 1
    ;;
esac
