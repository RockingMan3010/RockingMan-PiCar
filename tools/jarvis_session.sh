#!/usr/bin/env bash

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
STATE_DIR="$ROOT/.jarvis/session"
LOG_DIR="$ROOT/logs"

usage() {
    echo "Usage:"
    echo '  ./tools/jarvis_session.sh start "session goal"'
    echo '  ./tools/jarvis_session.sh status'
    echo '  ./tools/jarvis_session.sh end "what was achieved / learned"'
}

COMMAND="${1:-}"

if [ -z "$COMMAND" ]; then
    usage
    exit 2
fi

shift || true

case "$COMMAND" in

    start)
        if [ -d "$STATE_DIR" ]; then
            echo "A JARVIS session is already active."
            echo "Run:"
            echo "  ./tools/jarvis_session.sh status"
            exit 1
        fi

        mkdir -p "$STATE_DIR"

        date +%s > "$STATE_DIR/start_epoch"
        date --iso-8601=seconds > "$STATE_DIR/start_iso"

        git rev-parse --short HEAD > "$STATE_DIR/start_head"
        git branch --show-current > "$STATE_DIR/start_branch"
        git status --short > "$STATE_DIR/start_status"

        printf '%s\n' "$*" > "$STATE_DIR/goal"

        echo "JARVIS session started."
        echo
        echo "Goal: $*"
        echo "Branch: $(cat "$STATE_DIR/start_branch")"
        echo "HEAD: $(cat "$STATE_DIR/start_head")"
        echo "Started: $(cat "$STATE_DIR/start_iso")"
        ;;

    status)
        if [ ! -d "$STATE_DIR" ]; then
            echo "No active JARVIS session."
            exit 0
        fi

        START_EPOCH="$(cat "$STATE_DIR/start_epoch")"
        NOW_EPOCH="$(date +%s)"
        ELAPSED=$((NOW_EPOCH - START_EPOCH))
        MINUTES=$((ELAPSED / 60))

        echo "JARVIS session active."
        echo
        echo "Goal: $(cat "$STATE_DIR/goal")"
        echo "Started: $(cat "$STATE_DIR/start_iso")"
        echo "Start HEAD: $(cat "$STATE_DIR/start_head")"
        echo "Start branch: $(cat "$STATE_DIR/start_branch")"
        echo "Elapsed: ${MINUTES} min"
        echo
        echo "Current working tree:"
        git status --short
        ;;

    end)
        if [ ! -d "$STATE_DIR" ]; then
            echo "No active JARVIS session to end."
            exit 1
        fi

        if [ "$#" -lt 1 ]; then
            echo "Please provide an end-of-session summary."
            echo
            usage
            exit 2
        fi

        START_EPOCH="$(cat "$STATE_DIR/start_epoch")"
        START_ISO="$(cat "$STATE_DIR/start_iso")"
        START_HEAD="$(cat "$STATE_DIR/start_head")"
        START_BRANCH="$(cat "$STATE_DIR/start_branch")"
        START_STATUS="$(cat "$STATE_DIR/start_status")"
        GOAL="$(cat "$STATE_DIR/goal")"

        END_EPOCH="$(date +%s)"
        END_ISO="$(date --iso-8601=seconds)"
        END_HEAD="$(git rev-parse --short HEAD)"
        END_BRANCH="$(git branch --show-current)"

        DURATION_SEC=$((END_EPOCH - START_EPOCH))
        DURATION_MIN=$(((DURATION_SEC + 59) / 60))

        SUMMARY="$*"

        COMMITS="$(git log --oneline "${START_HEAD}..HEAD" 2>/dev/null || true)"
        END_STATUS="$(git status --short)"

        DAY="$(date +%F)"
        mkdir -p "$LOG_DIR"
        LOG_FILE="$LOG_DIR/$DAY.md"

        if [ ! -f "$LOG_FILE" ]; then
            {
                echo "# Engineering Log - $DAY"
                echo
                echo "Project: RockingMan PiCar-Pro Companion Robot"
            } > "$LOG_FILE"
        fi

        {
            echo
            echo "## JARVIS Session - $END_ISO"
            echo
            echo "**Goal:** ${GOAL:-Not specified}"
            echo
            echo "**Started:** $START_ISO"
            echo
            echo "**Ended:** $END_ISO"
            echo
            echo "**Duration:** ${DURATION_MIN} min"
            echo
            echo "**Branch:** \`$START_BRANCH\` → \`$END_BRANCH\`"
            echo
            echo "**HEAD:** \`$START_HEAD\` → \`$END_HEAD\`"
            echo
            echo "**Summary:** $SUMMARY"

            echo
            echo "**Commits created during session:**"
            echo
            echo '```text'

            if [ -n "$COMMITS" ]; then
                printf '%s\n' "$COMMITS"
            else
                echo "none"
            fi

            echo '```'

            echo
            echo "**Working tree at session start:**"
            echo
            echo '```text'

            if [ -n "$START_STATUS" ]; then
                printf '%s\n' "$START_STATUS"
            else
                echo "clean"
            fi

            echo '```'

            echo
            echo "**Working tree at session end:**"
            echo
            echo '```text'

            if [ -n "$END_STATUS" ]; then
                printf '%s\n' "$END_STATUS"
            else
                echo "clean"
            fi

            echo '```'
        } >> "$LOG_FILE"

        rm -rf "$STATE_DIR"

        echo "JARVIS session completed."
        echo
        echo "Duration: ${DURATION_MIN} min"
        echo "Start HEAD: $START_HEAD"
        echo "End HEAD:   $END_HEAD"
        echo "Log: $LOG_FILE"
        ;;

    *)
        usage
        exit 2
        ;;
esac
