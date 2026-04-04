#!/usr/bin/env node

// src/parallel-executor.ts
import { spawn } from "child_process";
import { readFileSync } from "fs";
var DEFAULT_MAX_CONCURRENCY = 4;
var DEFAULT_GLOBAL_TIMEOUT = 6e4;
async function executeHook(config, stdinData) {
  const name = config.name || config.command.split(" ").slice(0, 2).join(" ");
  const startTime = Date.now();
  const timeout = config.timeout || 3e4;
  return new Promise((resolve) => {
    const parts = config.command.split(" ");
    const cmd = parts[0] === "node" || parts[0] === "uv" ? parts[0] : parts[0];
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
    const timeoutId = setTimeout(() => {
      proc.kill();
      resolve({
        name,
        success: false,
        output: stdout,
        error: `Hook timed out after ${timeout}ms`,
        duration: Date.now() - startTime,
        timedOut: true
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
          timedOut: false
        });
      } else {
        resolve({
          name,
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
        name,
        success: false,
        output: "",
        error: err.message,
        duration: Date.now() - startTime,
        timedOut: false
      });
    });
    proc.stdin.write(stdinData);
    proc.stdin.end();
  });
}
async function executeParallel(config, stdinData) {
  const {
    hooks,
    maxConcurrency = DEFAULT_MAX_CONCURRENCY,
    globalTimeout = DEFAULT_GLOBAL_TIMEOUT,
    failFast = false,
    continueOnError = true
  } = config;
  const startTime = Date.now();
  const results = [];
  const globalTimeoutPromise = new Promise((_, reject) => {
    setTimeout(() => {
      reject(new Error(`Global timeout of ${globalTimeout}ms exceeded`));
    }, globalTimeout);
  });
  const executeWithConcurrency = async () => {
    const executing = [];
    const queue = [...hooks];
    const runNext = async () => {
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
    for (let i = 0; i < maxConcurrency; i++) {
      executing.push(runNext());
    }
    await Promise.all(executing);
  };
  try {
    await Promise.race([executeWithConcurrency(), globalTimeoutPromise]);
  } catch (err) {
    console.error(`Parallel execution error: ${err.message}`);
  }
  const totalDuration = Date.now() - startTime;
  const successfulOutputs = results.filter((r) => r.success && r.output).map((r) => r.output);
  const blockedHooks = [];
  for (const result of results) {
    if (result.success && result.output) {
      try {
        const parsed = JSON.parse(result.output);
        if (parsed.decision === "block" || parsed.result === "block") {
          blockedHooks.push(result.name);
        }
      } catch {
      }
    }
  }
  return {
    results,
    combinedOutput: successfulOutputs.join("\n"),
    hasErrors: results.some((r) => !r.success),
    totalDuration,
    blockedHooks
  };
}
function mergeOutputs(results) {
  const outputs = [];
  for (const result of results) {
    if (!result.success || !result.output) continue;
    try {
      const parsed = JSON.parse(result.output);
      outputs.push(parsed);
    } catch {
    }
  }
  if (outputs.length === 0) {
    return JSON.stringify({});
  }
  if (outputs.length === 1) {
    return JSON.stringify(outputs[0]);
  }
  const merged = {};
  for (const output of outputs) {
    for (const [key, value] of Object.entries(output)) {
      if (key === "hookSpecificOutput") {
        if (!merged.hookSpecificOutput) {
          merged.hookSpecificOutput = {};
        }
        const existing = merged.hookSpecificOutput;
        merged.hookSpecificOutput = { ...existing, ...value };
      } else {
        merged[key] = value;
      }
    }
  }
  return JSON.stringify(merged);
}
async function main() {
  const stdinData = readFileSync(0, "utf-8");
  const args = process.argv.slice(2);
  let hooks = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--hooks" && args[i + 1]) {
      try {
        const parsed = JSON.parse(args[i + 1]);
        hooks = Array.isArray(parsed) ? parsed : [parsed];
        i++;
      } catch (err) {
        console.error(`Failed to parse hooks config: ${err.message}`);
        process.exit(1);
      }
    }
  }
  if (hooks.length === 0) {
    console.error(`No hooks configured. Pass hooks with --hooks '[{"command": "..."}]'`);
    process.exit(1);
  }
  const config = {
    hooks,
    maxConcurrency: parseInt(process.env.PARALLEL_HOOKS_MAX_CONCURRENCY || "", 10) || DEFAULT_MAX_CONCURRENCY,
    globalTimeout: parseInt(process.env.PARALLEL_HOOKS_TIMEOUT || "", 10) || DEFAULT_GLOBAL_TIMEOUT,
    failFast: process.env.PARALLEL_HOOKS_FAIL_FAST === "true",
    continueOnError: process.env.PARALLEL_HOOKS_CONTINUE_ON_ERROR !== "false"
  };
  const aggregated = await executeParallel(config, stdinData);
  const mergedOutput = mergeOutputs(aggregated.results);
  if (process.env.PARALLEL_HOOKS_DEBUG === "true") {
    console.error(`[PARALLEL] Executed ${hooks.length} hooks in ${aggregated.totalDuration}ms`);
    for (const result of aggregated.results) {
      console.error(`[PARALLEL] ${result.name}: ${result.duration}ms (${result.success ? "OK" : "FAIL"})`);
    }
  }
  if (aggregated.blockedHooks.length > 0) {
    const errorMessages = aggregated.results.filter((r) => !r.success || aggregated.blockedHooks.includes(r.name)).map((r) => {
      try {
        const parsed = JSON.parse(r.output);
        return parsed.reason || parsed.message || r.error;
      } catch {
        return r.error || r.output;
      }
    }).filter(Boolean).join("\n\n");
    console.log(
      JSON.stringify({
        decision: "block",
        reason: errorMessages || `Blocked by: ${aggregated.blockedHooks.join(", ")}`
      })
    );
    return;
  }
  console.log(mergedOutput);
}
main().catch((err) => {
  console.error(`Parallel executor error: ${err.message}`);
  console.log(JSON.stringify({}));
  process.exit(1);
});
