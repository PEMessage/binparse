#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSER="$SCRIPT_DIR/binparser"

echo "=== 1. struct parser: default (colour + info) ==="
"$SCRIPT_DIR/test/gen_struct.py" -n 3 | uv run --script "$PARSER" -s struct -c none

echo ""
echo "=== 2. struct parser: --no-show-info ==="
"$SCRIPT_DIR/test/gen_struct.py" -n 3 | uv run --script "$PARSER" -s struct --no-show-info -c none

echo ""
echo "=== 3. struct parser: partial ==="
"$SCRIPT_DIR/test/gen_struct.py" -n 2 --partial | uv run --script "$PARSER" -s struct -c none

echo ""
echo "=== 4. file parser ==="
"$SCRIPT_DIR/test/gen_file.py" | uv run --script "$PARSER" -s file -c none

echo ""
echo "=== 5. file parser: --no-show-info ==="
"$SCRIPT_DIR/test/gen_file.py" | uv run --script "$PARSER" -s file --no-show-info -c none

echo ""
echo "=== 6. file parser: colours (-c fg / -c bg) ==="
"$SCRIPT_DIR/test/gen_file.py" | uv run --script "$PARSER" -s file -c fg 2>&1 | head -1
"$SCRIPT_DIR/test/gen_file.py" | uv run --script "$PARSER" -s file -c bg 2>&1 | head -1

echo ""
echo "=== All tests passed ==="
