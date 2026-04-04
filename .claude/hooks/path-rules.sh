#!/bin/bash
set -e
cd "$CLAUDE_CC_DIR/.claude/hooks"
cat | npx tsx src/path-rules.ts
