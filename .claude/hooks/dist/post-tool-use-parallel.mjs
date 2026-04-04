#!/usr/bin/env node

// src/post-tool-use-parallel.ts
import { readFileSync } from "fs";
import { spawn } from "child_process";
var HOME = process.env.HOME || process.env.USERPROFILE || "";
var CLAUDE_HOOKS_DIST = `${HOME}/.claude/hooks/dist`;
var POST_TOOL_USE_EDIT_HOOKS = [
  {
    name: "typescript-preflight",
    command: `node ${CLAUDE_HOOKS_DIST}/typescript-preflight.mjs`,
    timeout: 4e4
  },
  {
    name: "compiler-in-the-loop",
    command: `node ${CLAUDE_HOOKS_DIST}/compiler-in-the-loop.mjs`,
    timeout: 3e4
  },
  {
    name: "post-edit-notify",
    command: `node ${CLAUDE_HOOKS_DIST}/post-edit-notify.mjs`,
    timeout: 5e3
  },
  {
    name: "post-edit-diagnostics",
    command: `node ${CLAUDE_HOOKS_DIST}/post-edit-diagnostics.mjs`,
    timeout: 1e4
  },
  {
    name: "import-validator",
    command: `node ${CLAUDE_HOOKS_DIST}/import-validator.mjs`,
    timeout: 5e3
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
async function executeParallel(stdinData) {
  const startTime = Date.now();
  const promises = POST_TOOL_USE_EDIT_HOOKS.map(
    (hook) => executeHook(hook, stdinData)
  );
  const results = await Promise.all(promises);
  const totalDuration = Date.now() - startTime;
  if (process.env.PARALLEL_HOOKS_DEBUG === "true") {
    console.error(`[PARALLEL] Executed ${results.length} hooks in ${totalDuration}ms`);
    for (const result of results) {
      console.error(
        `[PARALLEL] ${result.name}: ${result.duration}ms (${result.success ? "OK" : "FAIL"})`
      );
    }
  }
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
  if (blockedHooks.length > 0) {
    const errorMessages = results.filter(
      (r) => !r.success || blockedHooks.includes(r.name)
    ).map((r) => {
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
        reason: errorMessages || `Blocked by: ${blockedHooks.join(", ")}`
      })
    );
    return;
  }
  const successfulOutputs = results.filter((r) => r.success && r.output).map((r) => r.output);
  if (successfulOutputs.length === 0) {
    console.log(JSON.stringify({}));
    return;
  }
  if (successfulOutputs.length === 1) {
    console.log(successfulOutputs[0]);
    return;
  }
  const merged = {};
  for (const output of successfulOutputs) {
    try {
      const parsed = JSON.parse(output);
      for (const [key, value] of Object.entries(parsed)) {
        if (key === "hookSpecificOutput") {
          if (!merged.hookSpecificOutput) {
            merged.hookSpecificOutput = {};
          }
          const existing = merged.hookSpecificOutput;
          merged.hookSpecificOutput = {
            ...existing,
            ...value
          };
        } else {
          merged[key] = value;
        }
      }
    } catch {
    }
  }
  console.log(JSON.stringify(merged));
}
async function main() {
  try {
    const stdinData = readFileSync(0, "utf-8");
    await executeParallel(stdinData);
  } catch (err) {
    console.error(`Parallel executor error: ${err.message}`);
    console.log(JSON.stringify({}));
    process.exit(1);
  }
}
main();
