#!/bin/bash
# Daily operations playbook for Intern Room
# Run this every morning to ensure system health

set -e

REPO_DIR="/home/remi/clawd/kigland-intern-room"
WORKSPACE_DIR="/home/remi/.openclaw/workspace"

echo "========================================"
echo "Intern Room Daily Operations"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# Step 1: Pull latest config
echo "📥 Step 1: Pulling latest configuration..."
cd "$REPO_DIR"
git pull --ff-only 2>/dev/null || echo "⚠️ Could not pull (may be offline or no remote)"
echo ""

# Step 2: Run health checks
echo "🔍 Step 2: Running health checks..."
if [ -x "$REPO_DIR/scripts/health/self-check.sh" ]; then
    "$REPO_DIR/scripts/health/self-check.sh" || echo "⚠️ Health checks found issues"
else
    echo "❌ Health check script not found"
fi
echo ""

# Step 3: Check yesterday's logs
echo "📊 Step 3: Reviewing yesterday's activity..."
YESTERDAY=$(date -d 'yesterday' '+%Y-%m-%d')
if [ -f "$REPO_DIR/logs/health-check.log" ]; then
    echo "Health check entries from yesterday:"
    grep "$YESTERDAY" "$REPO_DIR/logs/health-check.log" | tail -5 || echo "No entries found"
else
    echo "No health check log yet"
fi
echo ""

# Step 4: Verify all wip issues have activity
echo "📋 Step 4: Checking wip issues..."
cd "$REPO_DIR"
gh issue list --label "status:wip" --state open --json number,title,updatedAt | jq -r '.[] | "Issue #\(.number): \(.title) (updated: \(.updatedAt))"' 2>/dev/null || echo "Could not fetch issues"
echo ""

# Step 5: Summary
echo "✅ Daily operations complete"
echo "Next steps:"
echo "  - Review any alerts in $REPO_DIR/logs/alerts.pending"
echo "  - Address any P0 items immediately"
echo "  - Plan work for today"
echo "========================================"
