#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage:"
    echo '  ./tools/jarvis_log.sh "What you worked on / learned / fixed"'
    exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

DAY="$(date +%F)"
STAMP="$(date --iso-8601=seconds)"
LOG_DIR="$ROOT/logs"
LOG_FILE="$LOG_DIR/$DAY.md"

mkdir -p "$LOG_DIR"

SUMMARY="$*"
BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse --short HEAD)"
REMOTE="$(git remote get-url origin 2>/dev/null || echo 'none')"
STATUS="$(git status --short)"

if [ ! -f "$LOG_FILE" ]; then
    {
        echo "# Engineering Log - $DAY"
        echo
        echo "Project: RockingMan PiCar-Pro Companion Robot"
    } > "$LOG_FILE"
fi

{
    echo
    echo "## $STAMP"
    echo
    echo "**Summary:** $SUMMARY"
    echo
    echo "**Git branch:** \`$BRANCH\`"
    echo
    echo "**HEAD:** \`$HEAD\`"
    echo
    echo "**Remote:** \`$REMOTE\`"
    echo
    echo "**Working tree:**"
    echo
    echo '```text'

    if [ -n "$STATUS" ]; then
        printf '%s\n' "$STATUS"
    else
        echo "clean"
    fi

    echo '```'
} >> "$LOG_FILE"

echo "JARVIS engineering log updated:"
echo "$LOG_FILE"
