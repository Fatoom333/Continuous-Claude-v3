#!/bin/bash
# Impact Analysis for Refactoring Hook
# Uses TLDR daemon for fast cached impact analysis

exec node "$CLAUDE_CC_DIR/.claude/hooks/dist/impact-refactor.mjs"
