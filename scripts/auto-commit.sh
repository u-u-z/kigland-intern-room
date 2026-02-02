#!/bin/bash
# Auto-commit and push script for kigland-intern-room
# Run this periodically to sync changes to GitHub

set -e  # Exit on error

REPO_DIR="/home/remi/clawd/kigland-intern-room"
LOG_FILE="/tmp/auto-commit.log"

cd "$REPO_DIR" || {
    echo "[$(date)] ERROR: Cannot cd to $REPO_DIR" >> "$LOG_FILE"
    exit 1
}

echo "[$(date)] Starting auto-commit check..." >> "$LOG_FILE"

# Check git status
git_status=$(git status --porcelain 2>/dev/null || echo "ERROR")

if [ "$git_status" = "ERROR" ]; then
    echo "[$(date)] ERROR: git status failed" >> "$LOG_FILE"
    exit 1
fi

if [ -z "$git_status" ]; then
    echo "[$(date)] No changes to commit" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date)] Found changes:" >> "$LOG_FILE"
echo "$git_status" >> "$LOG_FILE"

# Generate commit message based on changed files
COMMIT_MSG="Auto-sync: $(date '+%Y-%m-%d %H:%M')"

# Detect change types
if echo "$git_status" | grep -q "research/intelligence/"; then
    COMMIT_MSG="$COMMIT_MSG | Daily intelligence update"
elif echo "$git_status" | grep -q "research/hacker-news/"; then
    COMMIT_MSG="$COMMIT_MSG | HN source tracking"
elif echo "$git_status" | grep -q "research/wip/"; then
    COMMIT_MSG="$COMMIT_MSG | Research WIP"
elif echo "$git_status" | grep -q "memory/"; then
    COMMIT_MSG="$COMMIT_MSG | Memory updates"
elif echo "$git_status" | grep -q "HEARTBEAT\|README\|\.md"; then
    COMMIT_MSG="$COMMIT_MSG | Config updates"
fi

# Add all changes (including new files)
git add -A
echo "[$(date)] Staged changes:" >> "$LOG_FILE"
git diff --cached --stat >> "$LOG_FILE" 2>&1 || true

# Commit
git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1
echo "[$(date)] Committed: $COMMIT_MSG" >> "$LOG_FILE"

# Push
git push origin main >> "$LOG_FILE" 2>&1
echo "[$(date)] Pushed to origin/main" >> "$LOG_FILE"

echo "[$(date)] Auto-commit complete" >> "$LOG_FILE"
