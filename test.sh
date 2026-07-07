#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSER="$SCRIPT_DIR/binparser"

echo "=== 1. demoA: default (colour + info) ==="
"$SCRIPT_DIR/test/gen_demoA.py" -n 3 | uv run --script "$PARSER" -s demoA -c none

echo ""
echo "=== 2. demoA: --no-show-info ==="
"$SCRIPT_DIR/test/gen_demoA.py" -n 3 | uv run --script "$PARSER" -s demoA --no-show-info -c none

echo ""
echo "=== 3. demoA: partial ==="
"$SCRIPT_DIR/test/gen_demoA.py" -n 2 --partial | uv run --script "$PARSER" -s demoA -c none

echo ""
echo "=== 4. demoB ==="
"$SCRIPT_DIR/test/gen_demoB.py" | uv run --script "$PARSER" -s demoB -c none

echo ""
echo "=== 5. demoB: --no-show-info ==="
"$SCRIPT_DIR/test/gen_demoB.py" | uv run --script "$PARSER" -s demoB --no-show-info -c none

echo ""
echo "=== 6. demoB: colours (-c fg / -c bg) ==="
"$SCRIPT_DIR/test/gen_demoB.py" | uv run --script "$PARSER" -s demoB -c fg 2>&1 | head -1
"$SCRIPT_DIR/test/gen_demoB.py" | uv run --script "$PARSER" -s demoB -c bg 2>&1 | head -1

echo ""
echo "=== All tests passed ==="
