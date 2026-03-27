#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
VENV="$ROOT/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -d "$VENV" ]]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

source "$VENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT/requirements.txt"

if [[ "${1:-}" == "--bootstrap-all" ]]; then
  python "$ROOT/scripts/bootstrap.py" --all
fi

echo
echo "Environment ready."
echo "Next steps:"
if [[ "${1:-}" == "--bootstrap-all" ]]; then
  echo "1. Run: python main.py --doctor"
  echo "2. Run: python main.py --once"
  echo "3. Run: python main.py --text \"open notepad\""
else
  echo "1. Run: python scripts/bootstrap.py --all"
  echo "2. Run: python main.py --doctor"
  echo "3. Run: python main.py --once"
fi
