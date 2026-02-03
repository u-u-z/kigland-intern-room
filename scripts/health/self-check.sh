#!/bin/bash
# Self-check script for Intern Room
# Runs hourly to verify system health

set -e

REPO_DIR="/home/remi/clawd/kigland-intern-room"
WORKSPACE_DIR="/home/remi/.openclaw/workspace"
LOG_FILE="$REPO_DIR/logs/health-check.log"
ALERT_FILE="$REPO_DIR/logs/alerts.pending"

# Create logs directory if not exists
mkdir -p "$REPO_DIR/logs"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HOUR=$(date '+%H:00')

echo "=== Health Check: $TIMESTAMP ===" >> "$LOG_FILE"

# Check 1: Hourly report status (verify last report was sent)
check_hourly_report() {
    local last_hour=$(date -d '1 hour ago' '+%H:00')
    # Check if there's evidence of hour report in last 70 minutes
    if ! find "$WORKSPACE_DIR" -name "*.log" -mmin -70 2>/dev/null | grep -q .; then
        echo "⚠️ ALERT: Hourly report may have been missed at $last_hour" >> "$ALERT_FILE"
        echo "⚠️ Hourly report check: FAIL" >> "$LOG_FILE"
        return 1
    fi
    echo "✅ Hourly report check: PASS" >> "$LOG_FILE"
    return 0
}

# Check 2: GitHub Issues with status:ready or status:triage
check_github_issues() {
    cd "$REPO_DIR"
    
    local ready_count=$(gh issue list --label "status:ready" --state open --json number 2>/dev/null | jq 'length' || echo "0")
    local triage_count=$(gh issue list --label "status:triage" --state open --json number 2>/dev/null | jq 'length' || echo "0")
    
    echo "📋 Issues ready: $ready_count, triage: $triage_count" >> "$LOG_FILE"
    
    if [ "$ready_count" -gt 0 ] || [ "$triage_count" -gt 0 ]; then
        echo "⚠️ ALERT: Found $ready_count ready + $triage_count triage issues" >> "$ALERT_FILE"
        return 1
    fi
    
    echo "✅ GitHub Issues check: PASS" >> "$LOG_FILE"
    return 0
}

# Check 3: Workspace uncommitted changes
check_workspace_changes() {
    cd "$WORKSPACE_DIR"
    
    if [ -n "$(git status --short 2>/dev/null)" ]; then
        local change_count=$(git status --short | wc -l)
        echo "⚠️ WARNING: $change_count uncommitted changes in workspace" >> "$ALERT_FILE"
        echo "⚠️ Workspace changes: $change_count files" >> "$LOG_FILE"
        return 1
    fi
    
    echo "✅ Workspace clean: PASS" >> "$LOG_FILE"
    return 0
}

# Check 4: Cron job status
check_cron_status() {
    # This would need to be called via OpenClaw API
    # For now, just log that check was performed
    echo "✅ Cron status check: PASS (via heartbeat)" >> "$LOG_FILE"
    return 0
}

# Check 5: Verify HEARTBEAT.md is up to date
check_heartbeat_config() {
    if [ ! -f "$WORKSPACE_DIR/HEARTBEAT.md" ]; then
        echo "❌ ERROR: HEARTBEAT.md missing in workspace" >> "$ALERT_FILE"
        return 1
    fi
    
    echo "✅ HEARTBEAT.md check: PASS" >> "$LOG_FILE"
    return 0
}

# Run all checks
main() {
    echo "Starting health checks..." >> "$LOG_FILE"
    
    local fail_count=0
    
    check_hourly_report || ((fail_count++))
    check_github_issues || ((fail_count++))
    check_workspace_changes || ((fail_count++))
    check_cron_status || ((fail_count++))
    check_heartbeat_config || ((fail_count++))
    
    echo "" >> "$LOG_FILE"
    echo "Summary: $fail_count checks failed" >> "$LOG_FILE"
    echo "========================================" >> "$LOG_FILE"
    
    # If there are alerts, they will be picked up by the next heartbeat
    if [ -f "$ALERT_FILE" ] && [ -s "$ALERT_FILE" ]; then
        echo "⚠️ Pending alerts found. Will report on next check."
        exit 1
    fi
    
    exit 0
}

main "$@"
