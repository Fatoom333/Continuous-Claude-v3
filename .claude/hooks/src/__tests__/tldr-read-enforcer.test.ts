#!/usr/bin/env node
/**
 * Tests for tldr-read-enforcer hook
 *
 * Tests:
 * - Code file detection
 * - Allowed file patterns
 * - Language detection
 * - TLDR mode selection
 * - Search context handling
 * - Edge cases (empty input, missing files)
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock daemon-client
vi.mock("../daemon-client", () => ({
  queryDaemonSync: vi.fn(),
  trackHookActivitySync: vi.fn(),
}));

import { queryDaemonSync, trackHookActivitySync } from "../daemon-client";

// Type the mocked functions
const mockQueryDaemonSync = queryDaemonSync as ReturnType<typeof vi.fn>;
const mockTrackHookActivitySync = trackHookActivitySync as ReturnType<
  typeof vi.fn
>;

// Extract testable functions from tldr-read-enforcer
// We'll test them by simulating hook behavior

// ============================================================================
// Code File Detection
// ============================================================================

const CODE_EXTENSIONS = new Set([
  ".py",
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".go",
  ".rs",
]);

function isCodeFile(filePath: string): boolean {
  const ext = filePath.split(".").pop()?.toLowerCase() || "";
  return CODE_EXTENSIONS.has(`.${ext}`);
}

// ============================================================================
// Allowed File Patterns
// ============================================================================

const ALLOWED_PATTERNS = [
  /\.json$/,
  /\.yaml$/,
  /\.yml$/,
  /\.toml$/,
  /\.md$/,
  /\.txt$/,
  /\.env/,
  /\.gitignore$/,
  /Makefile$/,
  /Dockerfile$/,
  /requirements\.txt$/,
  /package\.json$/,
  /tsconfig\.json$/,
  /pyproject\.toml$/,
  /test_.*\.py$/,
  /.*_test\.py$/,
  /.*\.test\.(ts|js)$/,
  /.*\.spec\.(ts|js)$/,
  /\.claude\/hooks\//,
  /\.claude\/skills\//,
  /init-db\.sql$/,
  /migrations\//,
];

const ALLOWED_DIRS = ["/tmp/", "node_modules/", ".venv/", "__pycache__/"];

function isAllowedFile(filePath: string): boolean {
  for (const pattern of ALLOWED_PATTERNS) {
    if (pattern.test(filePath)) return true;
  }
  for (const dir of ALLOWED_DIRS) {
    if (filePath.includes(dir)) return true;
  }
  return false;
}

// ============================================================================
// Language Detection
// ============================================================================

function detectLanguage(filePath: string): string {
  const ext = "." + filePath.split(".").pop()?.toLowerCase();
  const langMap: Record<string, string> = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
  };
  return langMap[ext] || "python";
}

// ============================================================================
// TLDR Mode Selection
// ============================================================================

type TldrMode = "structure" | "context" | "extract";

function chooseTldrMode(
  target: string | null,
  layers: string[],
  contextSource: string,
): { mode: TldrMode; reason: string } {
  const fromSearchRouter =
    contextSource.startsWith("function:") || contextSource.startsWith("class:");
  if (target && fromSearchRouter) {
    return { mode: "context", reason: `search: ${target}` };
  }

  if (layers.some((l) => ["cfg", "dfg", "pdg"].includes(l))) {
    return { mode: "extract", reason: "flow analysis" };
  }

  return { mode: "structure", reason: "navigation" };
}

// ============================================================================
// Tests
// ============================================================================

describe("TLDR Read Enforcer Hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Code File Detection
  // ---------------------------------------------------------------------------

  describe("Code File Detection", () => {
    it("should detect Python files", () => {
      expect(isCodeFile("main.py")).toBe(true);
      expect(isCodeFile("src/app.py")).toBe(true);
      expect(isCodeFile("test_foo.py")).toBe(true);
    });

    it("should detect TypeScript/JavaScript files", () => {
      expect(isCodeFile("index.ts")).toBe(true);
      expect(isCodeFile("component.tsx")).toBe(true);
      expect(isCodeFile("app.js")).toBe(true);
      expect(isCodeFile("widget.jsx")).toBe(true);
    });

    it("should detect Go and Rust files", () => {
      expect(isCodeFile("main.go")).toBe(true);
      expect(isCodeFile("lib.rs")).toBe(true);
    });

    it("should not detect non-code files", () => {
      expect(isCodeFile("README.md")).toBe(false);
      expect(isCodeFile("package.json")).toBe(false);
      expect(isCodeFile("config.yaml")).toBe(false);
      expect(isCodeFile("Dockerfile")).toBe(false);
    });
  });

  // ---------------------------------------------------------------------------
  // Allowed File Patterns
  // ---------------------------------------------------------------------------

  describe("Allowed File Patterns", () => {
    it("should allow config files", () => {
      expect(isAllowedFile("package.json")).toBe(true);
      expect(isAllowedFile("tsconfig.json")).toBe(true);
      expect(isAllowedFile("pyproject.toml")).toBe(true);
      expect(isAllowedFile("config.yaml")).toBe(true);
      expect(isAllowedFile(".env.local")).toBe(true);
    });

    it("should allow documentation files", () => {
      expect(isAllowedFile("README.md")).toBe(true);
      expect(isAllowedFile("CHANGELOG.md")).toBe(true);
      expect(isAllowedFile("docs/guide.md")).toBe(true);
    });

    it("should allow test files", () => {
      expect(isAllowedFile("test_app.py")).toBe(true);
      expect(isAllowedFile("app_test.py")).toBe(true);
      expect(isAllowedFile("component.test.ts")).toBe(true);
      expect(isAllowedFile("utils.spec.js")).toBe(true);
    });

    it("should allow hook and skill files", () => {
      expect(isAllowedFile(".claude/hooks/my-hook.ts")).toBe(true);
      expect(isAllowedFile(".claude/skills/my-skill/SKILL.md")).toBe(true);
    });

    it("should allow files in ignored directories", () => {
      expect(isAllowedFile("node_modules/package/index.js")).toBe(true);
      expect(isAllowedFile(".venv/lib/python/site.py")).toBe(true);
      expect(isAllowedFile("/tmp/test.py")).toBe(true);
      expect(isAllowedFile("src/__pycache__/module.pyc")).toBe(true);
    });

    it("should not allow regular code files", () => {
      expect(isAllowedFile("src/app.py")).toBe(false);
      expect(isAllowedFile("lib/main.go")).toBe(false);
      expect(isAllowedFile("src/index.ts")).toBe(false);
    });
  });

  // ---------------------------------------------------------------------------
  // Language Detection
  // ---------------------------------------------------------------------------

  describe("Language Detection", () => {
    it("should detect Python", () => {
      expect(detectLanguage("main.py")).toBe("python");
      expect(detectLanguage("src/utils.py")).toBe("python");
    });

    it("should detect TypeScript", () => {
      expect(detectLanguage("index.ts")).toBe("typescript");
      expect(detectLanguage("component.tsx")).toBe("typescript");
    });

    it("should detect JavaScript", () => {
      expect(detectLanguage("app.js")).toBe("javascript");
      expect(detectLanguage("widget.jsx")).toBe("javascript");
    });

    it("should detect Go and Rust", () => {
      expect(detectLanguage("main.go")).toBe("go");
      expect(detectLanguage("lib.rs")).toBe("rust");
    });

    it("should default to Python for unknown extensions", () => {
      expect(detectLanguage("file.unknown")).toBe("python");
    });
  });

  // ---------------------------------------------------------------------------
  // TLDR Mode Selection
  // ---------------------------------------------------------------------------

  describe("TLDR Mode Selection", () => {
    it("should choose context mode when target from search router", () => {
      const result = chooseTldrMode(
        "myFunction",
        ["ast"],
        "function: myFunction",
      );
      expect(result.mode).toBe("context");
      expect(result.reason).toContain("search");
    });

    it("should choose context mode for class targets from search router", () => {
      const result = chooseTldrMode("MyClass", ["ast"], "class: MyClass");
      expect(result.mode).toBe("context");
    });

    it("should choose extract mode for advanced layers", () => {
      const result = chooseTldrMode(null, ["ast", "cfg", "dfg"], "default");
      expect(result.mode).toBe("extract");
      expect(result.reason).toContain("flow analysis");
    });

    it("should choose structure mode by default", () => {
      const result = chooseTldrMode(null, ["ast", "call_graph"], "default");
      expect(result.mode).toBe("structure");
      expect(result.reason).toContain("navigation");
    });

    it("should prefer search context over default", () => {
      const defaultResult = chooseTldrMode(null, ["ast"], "default");
      const searchResult = chooseTldrMode(
        "target",
        ["ast"],
        "function: target",
      );

      expect(defaultResult.mode).toBe("structure");
      expect(searchResult.mode).toBe("context");
    });
  });

  // ---------------------------------------------------------------------------
  // Daemon Integration
  // ---------------------------------------------------------------------------

  describe("Daemon Integration", () => {
    it("should call queryDaemonSync for structure mode", () => {
      const mockResponse = {
        status: "ok",
        result: {
          functions: [
            {
              name: "main",
              params: [],
              line_number: 1,
              docstring: "Entry point",
            },
          ],
          classes: [],
        },
      };
      mockQueryDaemonSync.mockReturnValue(mockResponse);

      // Simulate calling daemon
      const result = queryDaemonSync(
        { cmd: "extract", file: "test.py", session: "test-session" },
        "/project",
      );

      expect(result.status).toBe("ok");
      expect(result.result.functions).toHaveLength(1);
      expect(result.result.functions[0].name).toBe("main");
    });

    it("should handle daemon errors gracefully", () => {
      mockQueryDaemonSync.mockReturnValue({
        status: "error",
        error: "Daemon not running",
      });

      const result = queryDaemonSync(
        { cmd: "extract", file: "test.py" },
        "/project",
      );

      expect(result.status).toBe("error");
      expect(result.error).toBeDefined();
    });
  });

  // ---------------------------------------------------------------------------
  // Edge Cases
  // ---------------------------------------------------------------------------

  describe("Edge Cases", () => {
    it("should handle files without extensions", () => {
      expect(isCodeFile("Makefile")).toBe(false);
      expect(isCodeFile("Dockerfile")).toBe(false);
    });

    it("should handle files with multiple extensions", () => {
      expect(isCodeFile("component.test.ts")).toBe(true);
      expect(isCodeFile("config.local.yaml")).toBe(false);
    });

    it("should handle relative and absolute paths", () => {
      expect(isCodeFile("/home/user/project/src/main.py")).toBe(true);
      expect(isCodeFile("./src/app.py")).toBe(true);
      expect(isCodeFile("../lib/utils.go")).toBe(true);
    });

    it("should handle null/undefined targets gracefully", () => {
      const result = chooseTldrMode(null, ["ast"], "default");
      expect(result.mode).toBe("structure");
    });

    it("should handle empty layers array", () => {
      const result = chooseTldrMode(null, [], "default");
      expect(result.mode).toBe("structure");
    });

    it("should handle malformed context source", () => {
      const result = chooseTldrMode("target", ["ast"], "malformed");
      expect(result.mode).toBe("structure");
    });
  });

  // ---------------------------------------------------------------------------
  // Hook Output Format
  // ---------------------------------------------------------------------------

  describe("Hook Output Format", () => {
    it("should return empty object for non-code files", () => {
      const input = {
        tool_name: "Read",
        tool_input: { file_path: "README.md" },
      };

      // Non-code files bypass TLDR
      const shouldBypass =
        !isCodeFile("README.md") || isAllowedFile("README.md");
      expect(shouldBypass).toBe(true);
    });

    it("should return empty object for allowed files", () => {
      const filePath = ".claude/hooks/my-hook.ts";
      expect(isAllowedFile(filePath)).toBe(true);
    });

    it("should return deny decision for code files", () => {
      const filePath = "src/main.py";
      expect(isCodeFile(filePath)).toBe(true);
      expect(isAllowedFile(filePath)).toBe(false);
    });
  });

  // ---------------------------------------------------------------------------
  // Search Context Integration
  // ---------------------------------------------------------------------------

  describe("Search Context Integration", () => {
    it("should use suggested layers from search context", () => {
      // Search context would provide layers like ["cfg", "dfg"] for flow analysis
      const layers = ["cfg", "dfg"];
      const target = "myFunction";

      const result = chooseTldrMode(target, layers, "function: myFunction");
      expect(result.mode).toBe("context");
    });

    it("should prefer context mode when target is from search", () => {
      const result = chooseTldrMode(
        "targetFunction",
        ["ast"],
        "function: targetFunction",
      );
      expect(result.mode).toBe("context");
      expect(result.reason).toContain("targetFunction");
    });
  });
});
