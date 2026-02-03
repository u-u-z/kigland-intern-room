#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="$ROOT_DIR/research/intelligence"
REPORT_FILE="$OUTPUT_DIR/daily-brief-$DATE.md"

mkdir -p "$OUTPUT_DIR"

echo "# Daily Intelligence Brief - $DATE" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Generated at $(date '+%H:%M:%S')" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. arXiv Fetcher
echo "## 1. arXiv Intelligence" >> "$REPORT_FILE"
echo "Running arXiv fetcher..."
if python3 "$SCRIPT_DIR/arxiv-daily-fetch.py" --output-dir "$ROOT_DIR/research/intelligence/arxiv-daily"; then
    ARXIV_FILE="$ROOT_DIR/research/intelligence/arxiv-daily/arxiv-$DATE.md"
    if [ -f "$ARXIV_FILE" ]; then
        echo "### arXiv Summary" >> "$REPORT_FILE"
        # Extract summary or top items? For now just link it
        echo "Full report: [arxiv-$DATE.md](file://$ARXIV_FILE)" >> "$REPORT_FILE"
        # Append the first few lines of the arxiv report
        head -n 20 "$ARXIV_FILE" | grep -v "^#" >> "$REPORT_FILE"
    else
        echo "No arXiv papers found today." >> "$REPORT_FILE"
    fi
else
    echo "Error running arXiv fetcher." >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# 2. Kigurumi Monitor (Placeholder)
echo "## 2. Kigurumi Market Monitor" >> "$REPORT_FILE"
echo "Status: Monitoring initialized (limited mode)." >> "$REPORT_FILE"
# python3 "$SCRIPT_DIR/kigurumi-monitor.py" ...

echo "" >> "$REPORT_FILE"

# 3. System Status
echo "## 3. System Status" >> "$REPORT_FILE"
echo "Disk Usage:" >> "$REPORT_FILE"
df -h . | tail -n 1 >> "$REPORT_FILE"

echo "Daily brief generated: $REPORT_FILE"
