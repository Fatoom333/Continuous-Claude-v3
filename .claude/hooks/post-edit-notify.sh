#!/bin/bash
# Post-Edit Notify Hook - notifies TLDR daemon of file changes
exec node "$CLAUDE_CC_DIR/.claude/hooks/dist/post-edit-notify.mjs"
