#!/usr/bin/env node
/**
 * PreToolUse Parallel Batch Executors
 *
 * Runs PreToolUse hooks in parallel for reduced latency.
 *
 * Executors:
 * - pre-tool-use-edit.mjs: file-claims, edit-context-inject, signature-helper (Edit)
 * - pre-tool-use-task.mjs: tldr-context-inject, arch-context-inject (Task)
 *
 * Performance improvements:
 *   Edit: 5s+5s+5s sequential → ~6s parallel (3 hooks)
 *   Task: 30s+30s sequential → ~32s parallel (2 hooks)
 */

import { readFileSync } from "fs";
import { spawn } from "child_process";

const HOME = process.env.HOME || process.env.USERPROFILE || "";
const CLAUDE_HOOKS_DIST = `${HOME}/.claude/hooks/dist`;

// PreToolUse Edit hooks (independent, can run in parallel)
const PRE_TOOL_USE_EDIT_HOOKS = [
  {
    name: "file-claims",
    command: `node ${CLAUDE_HOOKS_DIST}/file-claims.mjs`,
    timeout: 5000,
  },
  {
    name: "edit-context-inject",
    command: `node ${CLAUDE_HOOKS_DIST}/edit-context-inject.mjs`,
    timeout: 5000,
  },
  {
    name: "signature-helper",
    command: `node ${CLAUDE_HOOKS_DIST}/signature-helper.mjs`,
    timeout: 5000,
  },
];

// PreToolUse Task hooks (independent, can run in parallel)
const PRE_TOOL_USE_TASK_HOOKS = [
  {
    name: "tldr-context-inject",
    command: `node ${CLAUDE_HOOKS_DIST}/tldr-context-inject.mjs`,
    timeout: 30000,
  },
  {
    name: "arch-context-inject",
    command: `node ${CLAUDE_HOOKS_DIST}/arch-context-inject.mjs`,
    timeout: 30000,
  },
];

interface HookResult {
  name: string;
  success: boolean;
  output: string;
  error?: string;
  duration: number;
  timedOut: boolean;
}

interface EditHookOutput {
  hookSpecificOutput?: {
    hookEventName?: "PreToolUse";
    permissionDecision?: "allow" | "deny" | "ask";
    permissionDecisionReason?: string;
    updatedInput?: Record<string, unknown>;
  };
}

async function executeHook(
  config: { name: string; command: string; timeout: number },
  stdinData: string,
): Promise<HookResult> {
  const startTime = Date.now();

  return new Promise((resolve) => {
    const parts = config.command.split(" ");
    const cmd = parts[0];
    const args = parts.slice(1);

    const proc = spawn(cmd, args, {
      shell: true,
      env: { ...process.env },
      cwd: process.env.CLAUDE_CC_DIR || process.cwd(),
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
        timedOut: true,
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
          timedOut: false,
        });
      } else {
        resolve({
          name: config.name,
          success: false,
          output: stdout,
          error: stderr || `Hook exited with code ${code}`,
          duration,
          timedOut: false,
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
        timedOut: false,
      });
    });
  });
}

async function executeParallel(
  hooks: Array<{ name: string; command: string; timeout: number }>,
  stdinData: string,
): Promise<HookResult[]> {
  const promises = hooks.map((hook) => executeHook(hook, stdinData));
  return Promise.all(promises);
}

function mergeEditOutputs(results: HookResult[]): string {
  // For Edit hooks, merge updatedInput from all hooks
  const mergedOutput: EditHookOutput = {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
    },
  };

  let hasDeny = false;
  let denyReason = "";
  const updatedInputs: Record<string, unknown> = {};

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
      // Non-JSON output, skip
    }
  }

  if (hasDeny) {
    mergedOutput.hookSpecificOutput!.permissionDecision = "deny";
    mergedOutput.hookSpecificOutput!.permissionDecisionReason = denyReason;
  }

  if (Object.keys(updatedInputs).length > 0) {
    mergedOutput.hookSpecificOutput!.updatedInput = updatedInputs;
  }

  return JSON.stringify(mergedOutput);
}

function mergeTaskOutputs(results: HookResult[]): string {
  // For Task hooks, merge context injections
  const mergedOutput: Record<string, unknown> = {};
  const contexts: string[] = [];

  for (const result of results) {
    if (!result.success || !result.output) continue;

    try {
      const parsed = JSON.parse(result.output);
      if (parsed.hookSpecificOutput) {
        // Merge context
        if (parsed.hookSpecificOutput.updatedInput?.context) {
          contexts.push(parsed.hookSpecificOutput.updatedInput.context);
        }
      }
    } catch {
      // Non-JSON output, skip
    }
  }

  if (contexts.length > 0) {
    mergedOutput.hookSpecificOutput = {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      updatedInput: {
        context: contexts.join("\n\n---\n\n"),
      },
    };
  }

  return JSON.stringify(mergedOutput);
}

async function main(): Promise<void> {
  const stdinData = readFileSync(0, "utf-8");
  const args = process.argv.slice(2);

  // Determine which executor to use based on arg
  const executorType = args[0];

  let hooks: Array<{ name: string; command: string; timeout: number }>;
  let mergeFn: (results: HookResult[]) => string;

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

  // Log timing for observability
  if (process.env.PARALLEL_HOOKS_DEBUG === "true") {
    console.error(
      `[PARALLEL] Executed ${results.length} PreToolUse hooks in ${totalDuration}ms`,
    );
    for (const result of results) {
      console.error(
        `[PARALLEL] ${result.name}: ${result.duration}ms (${result.success ? "OK" : "FAIL"})`,
      );
    }
  }

  // Check for any blocking decisions
  for (const result of results) {
    if (result.success && result.output) {
      try {
        const parsed = JSON.parse(result.output);
        const hookOutput = parsed.hookSpecificOutput || parsed;
        if (hookOutput.permissionDecision === "deny") {
          // If any hook denies, return the deny decision
          console.log(
            JSON.stringify({
              hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason:
                  hookOutput.permissionDecisionReason ||
                  `Blocked by ${result.name}`,
              },
            }),
          );
          return;
        }
      } catch {
        // Continue on parse error
      }
    }
  }

  // All hooks passed or had errors - merge outputs
  const mergedOutput = mergeFn(results);
  console.log(mergedOutput);
}

main().catch((err) => {
  console.error(`PreToolUse parallel executor error: ${err.message}`);
  console.log(JSON.stringify({}));
  process.exit(1);
});
