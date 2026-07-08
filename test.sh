#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSER="$SCRIPT_DIR/binparser"

echo "=== 1. demoA ==="
"$SCRIPT_DIR/test/gen_demoA.py" -n 2 | uv run --script "$PARSER" -s demoA -c none

echo ""
echo "=== 2. demoB ==="
"$SCRIPT_DIR/test/gen_demoB.py" | uv run --script "$PARSER" -s demoB -c none

echo ""
echo "=== 3. asn1 ==="
"$SCRIPT_DIR/test/gen_asn1.py" | uv run --script "$PARSER" -s asn1 -c none

echo ""
echo "=== 4. asn1 --no-show-info ==="
"$SCRIPT_DIR/test/gen_asn1.py" | uv run --script "$PARSER" -s asn1 --no-show-info -c none

echo ""
echo "=== 5. asn1 cross-parser: demoA data → asn1 parser ==="
"$SCRIPT_DIR/test/gen_demoA.py" -n 1 | uv run --script "$PARSER" -s asn1 -c none

echo ""
echo "=== 6. asn1 --show-trailing ==="
"$SCRIPT_DIR/test/gen_demoA.py" -n 1 | uv run --script "$PARSER" -s asn1 --show-trailing -c none | tail -3

echo ""
echo "=== All tests passed ==="
