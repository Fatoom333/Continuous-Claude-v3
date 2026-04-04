#!/usr/bin/env node
/**
 * PostToolUse Parallel Batch Executor for Edit|Write
 *
 * Runs TypeScript and Lean compiler checks in parallel, then notifications.
 * Reduces sequential hook latency from ~90s to ~45s.
 *
 * Performance improvement:
 *   Before: typescript-preflight (40s) -> compiler-in-the-loop (30s) -> post-edit-notify (5s) -> post-edit-diagnostics (10s) -> import-validator (5s)
 *   After: parallel execution in ~45s (max of all hooks)
 *
 * Usage:
 *   node post-tool-use-parallel.mjs
 *
 * Environment variables:
 *   PARALLEL_HOOKS_DEBUG=true - Enable debug logging
 */

import { readFileSync } from "fs";
import { spawn } from "child_process";

const HOME = process.env.HOME || process.env.USERPROFILE || "";
const CLAUDE_HOOKS_DIST = `${HOME}/.claude/hooks/dist`;

const POST_TOOL_USE_EDIT_HOOKS = [
  {
    name: "typescript-preflight",
    command: `node ${CLAUDE_HOOKS_DIST}/typescript-preflight.mjs`,
    timeout: 40000,
  },
  {
    name: "compiler-in-the-loop",
    command: `node ${CLAUDE_HOOKS_DIST}/compiler-in-the-loop.mjs`,
    timeout: 30000,
  },
  {
    name: "post-edit-notify",
    command: `node ${CLAUDE_HOOKS_DIST}/post-edit-notify.mjs`,
    timeout: 5000,
  },
  {
    name: "post-edit-diagnostics",
    command: `node ${CLAUDE_HOOKS_DIST}/post-edit-diagnostics.mjs`,
    timeout: 10000,
  },
  {
    name: "import-validator",
    command: `node ${CLAUDE_HOOKS_DIST}/import-validator.mjs`,
    timeout: 5000,
  },
];

const MAX_CONCURRENCY = 4;
const GLOBAL_TIMEOUT = 60000;

interface HookResult {
  name: string;
  success: boolean;
  output: string;
  error?: string;
  duration: number;
  timedOut: boolean;
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

    // Write stdin
    proc.stdin.write(stdinData);
    proc.stdin.end();

    // Set timeout
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

async function executeParallel(stdinData: string): Promise<void> {
  const startTime = Date.now();

  // Execute all hooks in parallel
  const promises = POST_TOOL_USE_EDIT_HOOKS.map((hook) =>
    executeHook(hook, stdinData),
  );

  const results = await Promise.all(promises);
  const totalDuration = Date.now() - startTime;

  // Log timing for observability
  if (process.env.PARALLEL_HOOKS_DEBUG === "true") {
    console.error(
      `[PARALLEL] Executed ${results.length} hooks in ${totalDuration}ms`,
    );
    for (const result of results) {
      console.error(
        `[PARALLEL] ${result.name}: ${result.duration}ms (${result.success ? "OK" : "FAIL"})`,
      );
    }
  }

  // Find blocked hooks
  const blockedHooks: string[] = [];
  for (const result of results) {
    if (result.success && result.output) {
      try {
        const parsed = JSON.parse(result.output);
        if (parsed.decision === "block" || parsed.result === "block") {
          blockedHooks.push(result.name);
        }
      } catch {
        // Not JSON, skip
      }
    }
  }

  // If any hook blocked, return block decision with all error messages
  if (blockedHooks.length > 0) {
    const errorMessages = results
      .filter((r) => !r.success || blockedHooks.includes(r.name))
      .map((r) => {
        try {
          const parsed = JSON.parse(r.output);
          return parsed.reason || parsed.message || r.error;
        } catch {
          return r.error || r.output;
        }
      })
      .filter(Boolean)
      .join("\n\n");

    console.log(
      JSON.stringify({
        decision: "block",
        reason: errorMessages || `Blocked by: ${blockedHooks.join(", ")}`,
      }),
    );
    return;
  }

  // Merge outputs
  const successfulOutputs = results
    .filter((r) => r.success && r.output)
    .map((r) => r.output);

  if (successfulOutputs.length === 0) {
    console.log(JSON.stringify({}));
    return;
  }

  // If only one output, return it directly
  if (successfulOutputs.length === 1) {
    console.log(successfulOutputs[0]);
    return;
  }

  // Merge multiple outputs
  const merged: Record<string, unknown> = {};
  for (const output of successfulOutputs) {
    try {
      const parsed = JSON.parse(output);
      for (const [key, value] of Object.entries(parsed)) {
        if (key === "hookSpecificOutput") {
          if (!merged.hookSpecificOutput) {
            merged.hookSpecificOutput = {};
          }
          const existing = merged.hookSpecificOutput as Record<string, unknown>;
          merged.hookSpecificOutput = {
            ...existing,
            ...(value as Record<string, unknown>),
          };
        } else {
          merged[key] = value;
        }
      }
    } catch {
      // Non-JSON output, skip
    }
  }

  console.log(JSON.stringify(merged));
}

async function main(): Promise<void> {
  try {
    const stdinData = readFileSync(0, "utf-8");
    await executeParallel(stdinData);
  } catch (err) {
    console.error(`Parallel executor error: ${(err as Error).message}`);
    console.log(JSON.stringify({}));
    process.exit(1);
  }
}

main();
