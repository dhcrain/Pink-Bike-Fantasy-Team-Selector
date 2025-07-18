#!/bin/bash
# Usage: ./run_all.sh <html_file> [balance_factor] [keep_top_percent] [output_csv]

set -e
set -o pipefail

HTML_FILE="$1"
BALANCE_FACTOR="${2:-10.0}"
KEEP_TOP_PERCENT="${3:-30}"
OUTPUT_CSV="${4:-riders.csv}"
UCI_OUTPUT_CSV="${5:-uci-riders.csv}"


# Run the file parser with poetry
uv run python file_parser.py "$HTML_FILE" "$OUTPUT_CSV"
echo "File parsed successfully. Output saved to $OUTPUT_CSV"

uv run python merge_uci_results.py "$OUTPUT_CSV" "$UCI_OUTPUT_CSV"
echo "UCI results merged successfully. Output saved to $UCI_OUTPUT_CSV"

# Run the team selector with poetry
echo "Running team selector with UCI output (balance factor: $BALANCE_FACTOR, keep top: $KEEP_TOP_PERCENT%)"
uv run python team_selector.py "$UCI_OUTPUT_CSV" "$BALANCE_FACTOR" "$KEEP_TOP_PERCENT"
