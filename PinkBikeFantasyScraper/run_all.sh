#!/bin/bash
# Usage: ./run_all.sh <html_file> [output_csv]

set -e
set -o pipefail

HTML_FILE="$1"
OUTPUT_CSV="${2:-riders.csv}"
UCI_OUTPUT_CSV="${3:-uci-riders.csv}"

# Run the file parser with poetry
uv run python file_parser.py "$HTML_FILE" "$OUTPUT_CSV"
echo "File parsed successfully. Output saved to $OUTPUT_CSV"

uv run python merge_uci_results.py "$OUTPUT_CSV" "$UCI_OUTPUT_CSV"
echo "UCI results merged successfully. Output saved to $UCI_OUTPUT_CSV"

# Run the team selector with poetry
echo "Running team selector with UCI output"
uv run python team_selector.py "$UCI_OUTPUT_CSV"
