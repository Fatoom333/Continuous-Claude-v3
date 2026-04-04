#!/bin/bash
set -e
cd "$CLAUDE_CC_DIR/.claude/hooks"
cat | node dist/import-error-detector.mjs
