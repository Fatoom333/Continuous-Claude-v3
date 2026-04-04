#!/usr/bin/env node

// src/pre-tool-use-parallel.ts
import { readFileSync } from "fs";
import { spawn } from "child_process";
var HOME = process.env.HOME || process.env.USERPROFILE || "";
var CLAUDE_HOOKS_DIST = `${HOME}/.claude/hooks/dist`;
var PRE_TOOL_USE_EDIT_HOOKS = [
  {
    name: "file-claims",
    command: `node ${CLAUDE_HOOKS_DIST}/file-claims.mjs`,
    timeout: 5e3
  },
  {
    name: "edit-context-inject",
    command: `node ${CLAUDE_HOOKS_DIST}/edit-context-inject.mjs`,
    timeout: 5e3
  },
  {
    name: "signature-helper",
    command: `node ${CLAUDE_HOOKS_DIST}/signature-helper.mjs`,
    timeout: 5e3
  }
];
var PRE_TOOL_USE_TASK_HOOKS = [
  {
    name: "tldr-context-inject",
    command: `node ${CLAUDE_HOOKS_DIST}/tldr-context-inject.mjs`,
    timeout: 3e4
  },
  {
    name: "arch-context-inject",
    command: `node ${CLAUDE_HOOKS_DIST}/arch-context-inject.mjs`,
    timeout: 3e4
  }
];
async function executeHook(config, stdinData) {
  const startTime = Date.now();
  return new Promise((resolve) => {
    const parts = config.command.split(" ");
    const cmd = parts[0];
    const args = parts.slice(1);
    const proc = spawn(cmd, args, {
      shell: true,
      env: { ...process.env },
      cwd: process.env.CLAUDE_CC_DIR || process.cwd()
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });
    proc.stdin.write(stdinData);
    proc.stdin.end();
    const timeoutId = setTimeout(() => {
      proc.kill();
      resolve({
        name: config.name,
        success: false,
        output: stdout,
        error: `Hook timed out after ${config.timeout}ms`,
        duration: Date.now() - startTime,
        timedOut: true
      });
    }, config.timeout);
    proc.on("close", (code) => {
      clearTimeout(timeoutId);
      const duration = Date.now() - startTime;
      if (code === 0) {
        resolve({
          name: config.name,
          success: true,
          output: stdout,
          duration,
          timedOut: false
        });
      } else {
        resolve({
          name: config.name,
          success: false,
          output: stdout,
          error: stderr || `Hook exited with code ${code}`,
          duration,
          timedOut: false
        });
      }
    });
    proc.on("error", (err) => {
      clearTimeout(timeoutId);
      resolve({
        name: config.name,
        success: false,
        output: "",
        error: err.message,
        duration: Date.now() - startTime,
        timedOut: false
      });
    });
  });
}
async function executeParallel(hooks, stdinData) {
  const promises = hooks.map((hook) => executeHook(hook, stdinData));
  return Promise.all(promises);
}
function mergeEditOutputs(results) {
  const mergedOutput = {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow"
    }
  };
  let hasDeny = false;
  let denyReason = "";
  const updatedInputs = {};
  for (const result of results) {
    if (!result.success || !result.output) continue;
    try {
      const parsed = JSON.parse(result.output);
      const hookOutput = parsed.hookSpecificOutput || parsed;
      if (hookOutput.permissionDecision === "deny") {
        hasDeny = true;
        denyReason = hookOutput.permissionDecisionReason || denyReason;
      }
      if (hookOutput.updatedInput) {
        Object.assign(updatedInputs, hookOutput.updatedInput);
      }
    } catch {
    }
  }
  if (hasDeny) {
    mergedOutput.hookSpecificOutput.permissionDecision = "deny";
    mergedOutput.hookSpecificOutput.permissionDecisionReason = denyReason;
  }
  if (Object.keys(updatedInputs).length > 0) {
    mergedOutput.hookSpecificOutput.updatedInput = updatedInputs;
  }
  return JSON.stringify(mergedOutput);
}
function mergeTaskOutputs(results) {
  const mergedOutput = {};
  const contexts = [];
  for (const result of results) {
    if (!result.success || !result.output) continue;
    try {
      const parsed = JSON.parse(result.output);
      if (parsed.hookSpecificOutput) {
        if (parsed.hookSpecificOutput.updatedInput?.context) {
          contexts.push(parsed.hookSpecificOutput.updatedInput.context);
        }
      }
    } catch {
    }
  }
  if (contexts.length > 0) {
    mergedOutput.hookSpecificOutput = {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      updatedInput: {
        context: contexts.join("\n\n---\n\n")
      }
    };
  }
  return JSON.stringify(mergedOutput);
}
async function main() {
  const stdinData = readFileSync(0, "utf-8");
  const args = process.argv.slice(2);
  const executorType = args[0];
  let hooks;
  let mergeFn;
  if (executorType === "edit") {
    hooks = PRE_TOOL_USE_EDIT_HOOKS;
    mergeFn = mergeEditOutputs;
  } else if (executorType === "task") {
    hooks = PRE_TOOL_USE_TASK_HOOKS;
    mergeFn = mergeTaskOutputs;
  } else {
    console.error(`Usage: ${process.argv[1]} <edit|task>`);
    console.error("  edit - Run PreToolUse Edit hooks in parallel");
    console.error("  task - Run PreToolUse Task hooks in parallel");
    process.exit(1);
    return;
  }
  const startTime = Date.now();
  const results = await executeParallel(hooks, stdinData);
  const totalDuration = Date.now() - startTime;
  if (process.env.PARALLEL_HOOKS_DEBUG === "true") {
    console.error(`[PARALLEL] Executed ${results.length} PreToolUse hooks in ${totalDuration}ms`);
    for (const result of results) {
      console.error(
        `[PARALLEL] ${result.name}: ${result.duration}ms (${result.success ? "OK" : "FAIL"})`
      );
    }
  }
  for (const result of results) {
    if (result.success && result.output) {
      try {
        const parsed = JSON.parse(result.output);
        const hookOutput = parsed.hookSpecificOutput || parsed;
        if (hookOutput.permissionDecision === "deny") {
          console.log(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: "PreToolUse",
              permissionDecision: "deny",
              permissionDecisionReason: hookOutput.permissionDecisionReason || `Blocked by ${result.name}`
            }
          }));
          return;
        }
      } catch {
      }
    }
  }
  const mergedOutput = mergeFn(results);
  console.log(mergedOutput);
}
main().catch((err) => {
  console.error(`PreToolUse parallel executor error: ${err.message}`);
  console.log(JSON.stringify({}));
  process.exit(1);
});
