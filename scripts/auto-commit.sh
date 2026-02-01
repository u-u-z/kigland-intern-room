#!/bin/bash
# Auto-commit and push script for kigland-intern-room
# Run this periodically to sync changes to GitHub

REPO_DIR="/home/remi/clawd/kigland-intern-room"
cd "$REPO_DIR" || exit 1

# Check if there are changes
if git diff --quiet && git diff --staged --quiet && [ -z "$(git status --porcelain)" ]; then
    # No changes
    exit 0
fi

# Generate commit message based on changed files
CHANGES=$(git status --porcelain | head -10)
COMMIT_MSG="Auto-sync: $(date '+%Y-%m-%d %H:%M')"

# Add specific context based on what changed
if echo "$CHANGES" | grep -q "research/intelligence/"; then
    COMMIT_MSG="$COMMIT_MSG | Daily intelligence update"
fi

if echo "$CHANGES" | grep -q "research/hacker-news/"; then
    COMMIT_MSG="$COMMIT_MSG | HN source tracking"
fi

if echo "$CHANGES" | grep -q "memory/"; then
    COMMIT_MSG="$COMMIT_MSG | Memory updates"
fi

# Add all changes and commit
git add -A
git commit -m "$COMMIT_MSG" || exit 0

# Push to origin
git push origin main
