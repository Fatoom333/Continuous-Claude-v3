#!/usr/bin/env node
/**
 * Parallel Hook Executor
 *
 * Runs multiple hooks in parallel with aggregated results.
 * Reduces sequential hook chain latency by executing independent hooks concurrently.
 *
 * Usage:
 *   node parallel-executor.mjs --hooks '["hook1", "hook2", "hook3"]'
 *
 * Configuration (via environment variables):
 *   PARALLEL_HOOKS_MAX_CONCURRENCY - Max parallel hooks (default: 4)
 *   PARALLEL_HOOKS_TIMEOUT - Global timeout in ms (default: 60000)
 *   PARALLEL_HOOKS_FAIL_FAST - Stop on first error (default: false)
 */

import { spawn } from "child_process";
import { readFileSync } from "fs";

interface HookConfig {
  command: string;
  timeout?: number;
  name?: string;
}

interface HookResult {
  name: string;
  success: boolean;
  output: string;
  error?: string;
  duration: number;
  timedOut: boolean;
}

interface ParallelExecutorConfig {
  hooks: HookConfig[];
  maxConcurrency?: number;
  globalTimeout?: number;
  failFast?: boolean;
  continueOnError?: boolean;
}

interface AggregatedResult {
  results: HookResult[];
  combinedOutput: string;
  hasErrors: boolean;
  totalDuration: number;
  blockedHooks: string[];
}

const DEFAULT_MAX_CONCURRENCY = 4;
const DEFAULT_GLOBAL_TIMEOUT = 60000;

/**
 * Execute a single hook command.
 */
async function executeHook(
  config: HookConfig,
  stdinData: string,
): Promise<HookResult> {
  const name = config.name || config.command.split(" ").slice(0, 2).join(" ");
  const startTime = Date.now();
  const timeout = config.timeout ||30000;

  return new Promise((resolve) => {
    const parts = config.command.split(" ");
    const cmd = parts[0] === "node" || parts[0] === "uv" ? parts[0] : parts[0];
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

    // Set timeout
    const timeoutId = setTimeout(() => {
      proc.kill();
      resolve({
      name,
        success: false,
        output: stdout,
        error: `Hook timed out after ${timeout}ms`,
        duration: Date.now() - startTime,
        timedOut: true,
      });
    }, timeout);

    proc.on("close", (code) => {
      clearTimeout(timeoutId);
      const duration = Date.now() - startTime;

      if (code === 0) {
        resolve({
          name,
          success: true,
          output: stdout,
          duration,
          timedOut: false,
        });
      } else {
        resolve({
          name,
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
        name,
        success: false,
        output: "",
        error: err.message,
        duration: Date.now() - startTime,
        timedOut: false,
      });
    });

    // Pass stdin data to the hook
    proc.stdin.write(stdinData);
    proc.stdin.end();
  });
}

/**
 * Execute multiple hooks in parallel with concurrency limit.
 */
async function executeParallel(
  config: ParallelExecutorConfig,
  stdinData: string,
): Promise<AggregatedResult> {
  const {
    hooks,
    maxConcurrency = DEFAULT_MAX_CONCURRENCY,
    globalTimeout = DEFAULT_GLOBAL_TIMEOUT,
    failFast = false,
    continueOnError = true,
  } = config;

  const startTime = Date.now();
  const results: HookResult[] = [];

  // Global timeout wrapper
  const globalTimeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => {
      reject(new Error(`Global timeout of ${globalTimeout}ms exceeded`));
    }, globalTimeout);
  });

  // Execute hooks with concurrency limit
  const executeWithConcurrency = async (): Promise<void> => {
    const executing: Promise<void>[] = [];
    const queue = [...hooks];

    const runNext = async (): Promise<void> => {
      while (queue.length > 0) {
        const hook = queue.shift();
        if (!hook) break;

        const result = await executeHook(hook, stdinData);
        results.push(result);

        if (!result.success && failFast) {
          throw new Error(`Hook ${result.name} failed: ${result.error}`);
        }
      }
    };

    // Start concurrent workers
    for (let i = 0; i < maxConcurrency; i++) {
      executing.push(runNext());
    }

    await Promise.all(executing);
  };

  try {
    await Promise.race([executeWithConcurrency(), globalTimeoutPromise]);
  } catch (err) {
    // Return partial results on error
    console.error(`Parallel execution error: ${(err as Error).message}`);
  }

  const totalDuration = Date.now() - startTime;

  // Combine outputs from successful hooks
  const successfulOutputs = results
    .filter((r) => r.success && r.output)
    .map((r) => r.output);

  // Find blocked hooks (hooks that returned block decision)
  const blockedHooks: string[] = [];
  for (const result of results) {
    if (result.success && result.output) {
      try {
        const parsed = JSON.parse(result.output);
        if (parsed.decision === "block" || parsed.result === "block") {
          blockedHooks.push(result.name);
        }
      } catch {
        // NotJSON, skip
      }
    }
  }

  return {
    results,
    combinedOutput: successfulOutputs.join("\n"),
    hasErrors: results.some((r) => !r.success),
    totalDuration,
    blockedHooks,
  };
}

/**
 * Merge hook outputs intelligently.
 */
function mergeOutputs(results: HookResult[]): string {
  const outputs: Record<string, unknown>[] = [];

  for (const result of results) {
    if (!result.success || !result.output) continue;

    try {
      const parsed = JSON.parse(result.output);
      outputs.push(parsed);
    } catch {
      // Non-JSON output, skip
    }
  }

  if (outputs.length === 0) {
    return JSON.stringify({});
  }

  if (outputs.length === 1) {
    return JSON.stringify(outputs[0]);
  }

  // Merge multiple outputs
  const merged: Record<string, unknown> = {};

  for (const output of outputs) {
    for (const [key, value] of Object.entries(output)) {
      if (key === "hookSpecificOutput") {
        // Handle hook-specific outputs
        if (!merged.hookSpecificOutput) {
          merged.hookSpecificOutput = {};
        }
        // Merge with existing
        const existing = merged.hookSpecificOutput as Record<string, unknown>;
        merged.hookSpecificOutput = { ...existing, ...(value as Record<string, unknown>) };
      } else {
        merged[key] = value;
      }
    }
  }

  return JSON.stringify(merged);
}

/**
 * Main entry point.
 */
async function main(): Promise<void> {
  // Read stdin (hook input from Claude Code)
  const stdinData = readFileSync(0, "utf-8");

  // Parse hook configuration from CLI args
  const args = process.argv.slice(2);
  let hooks: HookConfig[] = [];

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--hooks" && args[i + 1]) {
      try {
        const parsed = JSON.parse(args[i + 1]);
        hooks = Array.isArray(parsed) ? parsed : [parsed];
        i++;
      } catch (err) {
        console.error(`Failed to parse hooks config: ${(err as Error).message}`);
        process.exit(1);
      }
    }
  }

  if (hooks.length === 0) {
    console.error("No hooks configured. Pass hooks with --hooks '[{\"command\": \"...\"}]'");
    process.exit(1);
  }

  // Get configuration from environment
  const config: ParallelExecutorConfig = {
    hooks,
    maxConcurrency:
      parseInt(process.env.PARALLEL_HOOKS_MAX_CONCURRENCY || "", 10) ||
      DEFAULT_MAX_CONCURRENCY,
    globalTimeout:
      parseInt(process.env.PARALLEL_HOOKS_TIMEOUT || "", 10) ||
      DEFAULT_GLOBAL_TIMEOUT,
    failFast: process.env.PARALLEL_HOOKS_FAIL_FAST === "true",
    continueOnError: process.env.PARALLEL_HOOKS_CONTINUE_ON_ERROR !== "false",
  };

  // Execute hooks in parallel
  const aggregated = await executeParallel(config, stdinData);

  // Output merged result
  const mergedOutput = mergeOutputs(aggregated.results);

  // Log timing for observability
  if (process.env.PARALLEL_HOOKS_DEBUG === "true") {
    console.error(`[PARALLEL] Executed ${hooks.length} hooks in ${aggregated.totalDuration}ms`);
    for (const result of aggregated.results) {
      console.error(`[PARALLEL] ${result.name}: ${result.duration}ms (${result.success ? "OK" : "FAIL"})`);
    }
  }

  // If any hook blocked, return block decision with all error messages
  if (aggregated.blockedHooks.length > 0) {
    const errorMessages = aggregated.results
      .filter((r) => !r.success || aggregated.blockedHooks.includes(r.name))
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
        reason: errorMessages || `Blocked by: ${aggregated.blockedHooks.join(", ")}`,
      })
    );
    return;
  }

  // Return merged output
  console.log(mergedOutput);
}

main().catch((err) => {
  console.error(`Parallel executor error: ${err.message}`);
  console.log(JSON.stringify({})); // Empty output on error
  process.exit(1);
});