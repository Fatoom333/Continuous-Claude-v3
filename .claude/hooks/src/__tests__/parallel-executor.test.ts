#!/usr/bin/env node
/**
 * Test script for Parallel Hook Executor
 *
 * Tests:
 * 1. Single hook execution
 * 2. Multiple parallel hooks
 * 3. Error handling
 * 4. Timeout handling
 * 5. Output merging
 */

import { spawn } from "child_process";
import { writeFileSync, mkdtempSync, rmdirSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";

const TEST_CASES = [
  {
    name: "Single hook success",
    config: {
      hooks: [
        {
          command: 'echo \'{"test": "pass"}\'',
          timeout: 5000,
          name: "echo-test",
        },
      ],
    },
    expected: {
      hasErrors: false,
      blockedHooks: [],
      resultCount: 1,
    },
  },
  {
    name: "Multiple parallel hooks",
    config: {
      hooks: [
        {
          command: 'echo \'{"test": "one"}\'',
          timeout: 5000,
          name: "hook-one",
        },
        {
          command: 'echo \'{"test": "two"}\'',
          timeout: 5000,
          name: "hook-two",
        },
        {
          command: 'echo \'{"test": "three"}\'',
          timeout: 5000,
          name: "hook-three",
        },
      ],
      maxConcurrency: 2,
    },
    expected: {
      hasErrors: false,
      blockedHooks: [],
      resultCount: 3,
    },
  },
  {
    name: "Hook failure handling",
    config: {
      hooks: [
        {
          command: 'echo \'{"test": "pass"}\'',
          timeout: 5000,
          name: "passing-hook",
        },
        {
          command: "exit 1",
          timeout: 5000,
          name: "failing-hook",
        },
      ],
      continueOnError: true,
    },
    expected: {
      hasErrors: true,
      blockedHooks: [],
      resultCount: 2,
    },
  },
  {
    name: "Block decision merging",
    config: {
      hooks: [
        {
          command: 'echo \'{"decision": "block", "reason": "Test block"}\'',
          timeout: 5000,
          name: "blocking-hook",
        },
      ],
    },
    expected: {
      hasErrors: false,
      blockedHooks: ["blocking-hook"],
      resultCount: 1,
    },
  },
  {
    name: "Timeout handling",
    config: {
      hooks: [
        {
          command: "sleep 10",
          timeout: 100,
          name: "timeout-hook",
        },
      ],
    },
    expected: {
      hasErrors: true,
      blockedHooks: [],
      resultCount: 1,
      hasTimeout: true,
    },
  },
];

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  duration: number;
}

async function runTest(testCase: (typeof TEST_CASES)[0]): Promise<TestResult> {
  const startTime = Date.now();
  const tempDir = mkdtempSync(join(tmpdir(), "parallel-test-"));
  const inputFile = join(tempDir, "input.json");

  // Write test input
  writeFileSync(inputFile, JSON.stringify({ test: "input" }));

  return new Promise((resolve) => {
    const args = [
      "dist/parallel-executor.mjs",
      "--hooks",
      JSON.stringify(testCase.config.hooks),
    ];

    const proc = spawn("node", args, {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PARALLEL_HOOKS_MAX_CONCURRENCY: String(
          testCase.config.maxConcurrency || 4,
        ),
        PARALLEL_HOOKS_TIMEOUT: String(testCase.config.timeout || 60000),
        PARALLEL_HOOKS_CONTINUE_ON_ERROR:
          testCase.config.continueOnError !== false ? "true" : "false",
        PARALLEL_HOOKS_DEBUG: "true",
      },
    });

    let stdout = "";
    let stderr = "";

    proc.stdin.write(JSON.stringify({ test: "input" }));
    proc.stdin.end();

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      const duration = Date.now() - startTime;

      try {
        // Clean up
        try {
          rmdirSync(tempDir, { recursive: true });
        } catch {
          // Ignore cleanup errors
        }

        // Parse output
        const output = JSON.parse(stdout);

        // Verify expectations
        const errors: string[] = [];

        if (testCase.expected.hasErrors !== undefined) {
          const actualHasErrors = output.hasErrors || code !== 0;
          if (actualHasErrors !== testCase.expected.hasErrors) {
            errors.push(
              `hasErrors: expected ${testCase.expected.hasErrors}, got ${actualHasErrors}`,
            );
          }
        }

        if (testCase.expected.blockedHooks !== undefined) {
          const actualBlocked = output.blockedMocks || [];
          if (
            JSON.stringify(actualBlocked.sort()) !==
            JSON.stringify(testCase.expected.blockedHooks.sort())
          ) {
            errors.push(
              `blockedHooks: expected ${JSON.stringify(testCase.expected.blockedHooks)}, got ${JSON.stringify(actualBlocked)}`,
            );
          }
        }

        if (testCase.expected.resultCount !== undefined) {
          if (output.results?.length !== testCase.expected.resultCount) {
            errors.push(
              `resultCount: expected ${testCase.expected.resultCount}, got ${output.results?.length}`,
            );
          }
        }

        if (testCase.expected.hasTimeout) {
          const hasTimeout = output.results?.some(
            (r: { timedOut?: boolean }) => r.timedOut,
          );
          if (!hasTimeout) {
            errors.push("Expected timeout but none detected");
          }
        }

        if (errors.length > 0) {
          resolve({
            name: testCase.name,
            passed: false,
            error: errors.join("; "),
            duration,
          });
        } else {
          resolve({
            name: testCase.name,
            passed: true,
            duration,
          });
        }
      } catch (err) {
        resolve({
          name: testCase.name,
          passed: false,
          error: `Failed to parse output: ${(err as Error).message}\nstdout: ${stdout}\nstderr: ${stderr}`,
          duration,
        });
      }
    });

    proc.on("error", (err) => {
      resolve({
        name: testCase.name,
        passed: false,
        error: `Process error: ${err.message}`,
        duration: Date.now() - startTime,
      });
    });
  });
}

async function main(): Promise<void> {
  console.log("Running Parallel Hook Executor Tests\n");
  console.log("=".repeat(60));

  const results: TestResult[] = [];

  for (const testCase of TEST_CASES) {
    console.log(`\nTest: ${testCase.name}`);
    const result = await runTest(testCase);
    results.push(result);

    if (result.passed) {
      console.log(`  ✓ PASSED (${result.duration}ms)`);
    } else {
      console.log(`  ✗ FAILED: ${result.error}`);
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("\nTest Summary:");
  console.log(`  Total: ${results.length}`);
  console.log(`  Passed: ${results.filter((r) => r.passed).length}`);
  console.log(`  Failed: ${results.filter((r) => !r.passed).length}`);

  const failed = results.filter((r) => !r.passed);
  if (failed.length > 0) {
    console.log("\nFailed tests:");
    for (const f of failed) {
      console.log(`  - ${f.name}: ${f.error}`);
    }
    process.exit(1);
  }

  console.log("\n✓ All tests passed!");
  process.exit(0);
}

main().catch((err) => {
  console.error(`Test runner error: ${err.message}`);
  process.exit(1);
});
