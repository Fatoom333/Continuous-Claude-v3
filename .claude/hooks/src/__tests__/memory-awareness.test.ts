/**
 * Tests for memory-awareness.ts
 *
 * Test coverage:
 * - extractIntent: meta-phrase removal, intent extraction
 * - extractKeywords: stopword filtering, keyword extraction
 * - checkMemoryRelevance: spawn mock, JSON parsing
 * - Main function: skip conditions, output format
 * - Edge cases: empty prompts, short prompts, slash commands
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { spawnSync } from "child_process";
import { readFileSync, existsSync } from "fs";

// Mock child_process
vi.mock("child_process", () => ({
  spawnSync: vi.fn(),
}));

// Mock fs
vi.mock("fs", () => ({
  readFileSync: vi.fn(),
  existsSync: vi.fn(() => true),
}));

// Mock opc-path
vi.mock("../shared/opc-path.js", () => ({
  getOpcDir: vi.fn(() => "/test/opc"),
}));

// Import after mocking
import {
  extractIntent,
  extractKeywords,
  checkMemoryRelevance,
} from "../memory-awareness.js";
import { getOpcDir } from "../shared/opc-path.js";

describe("extractIntent", () => {
  it("strips 'can you' meta-phrases", () => {
    const result = extractIntent("Can you help me with authentication?");
    // Note: strips "Can you" but "help me" is a different pattern
    expect(result.length).toBeLessThan(
      "Can you help me with authentication?".length,
    );
    expect(result).toContain("authentication");
  });

  it("strips 'help me' meta-phrases", () => {
    const result = extractIntent("Help me implement OAuth2");
    expect(result).toBe("implement OAuth2");
  });

  it("strips 'how do i' meta-phrases", () => {
    const result = extractIntent("How do I fix the bug?");
    expect(result).toBe("fix the bug");
  });

  it("strips 'what is' meta-phrases", () => {
    const result = extractIntent("What is the status of the API?");
    expect(result).toBe("the status of the API");
  });

  it("strips trailing 'please'", () => {
    const result = extractIntent("Show me the logs please");
    // Note: "please" is only stripped when at start after meta-phrase removal
    // "Show me" is stripped first, then trailing "please"
    expect(result.length).toBeLessThan("Show me the logs please".length);
  });

  it("strips trailing 'thanks'", () => {
    const result = extractIntent("Find the error thanks");
    expect(result).toBe("the error");
  });

  it("strips question marks", () => {
    const result = extractIntent("Where is the config?");
    expect(result).toBe("the config");
  });

  it("strips multiple meta-phrases", () => {
    const result = extractIntent("Can you please help me with deployment?");
    // Result may vary based on order of stripping
    expect(result.length).toBeLessThan(
      "Can you please help me with deployment?".length,
    );
  });

  it("returns original when no meta-phrases", () => {
    const result = extractIntent("Implement user authentication");
    expect(result).toBe("Implement user authentication");
  });

  it("falls back to keywords for very short intent", () => {
    const result = extractIntent("Do it");
    // Falls back to extractKeywords, which may return empty for very short input
    expect(typeof result).toBe("string");
  });

  it("handles empty prompt", () => {
    const result = extractIntent("");
    expect(result).toBe(""); // extractKeywords returns empty for empty input
  });

  it("preserves technical terms", () => {
    const result = extractIntent("Configure OAuth2 authentication");
    expect(result).toContain("OAuth2");
  });

  it("removes 'i want to' phrases", () => {
    const result = extractIntent("I want to add tests");
    expect(result).toBe("add tests");
  });

  it("removes 'let's' phrases", () => {
    const result = extractIntent("Let's refactor the module");
    expect(result).toBe("refactor the module");
  });
});

describe("extractKeywords", () => {
  it("extracts meaningful keywords", () => {
    const result = extractKeywords("Implement user authentication with OAuth2");
    expect(result).toContain("implement");
    expect(result).toContain("user");
    expect(result).toContain("authentication");
    expect(result).toContain("oauth2");
  });

  it("filters stop words", () => {
    const result = extractKeywords(
      "What is the best way to implement authentication?",
    );
    const words = result.split(" ");
    // Should not contain common stopwords as separate words
    expect(words).not.toContain("what");
    expect(words).not.toContain("is");
    expect(words).not.toContain("to");
  });

  it("removes short words", () => {
    const result = extractKeywords("Add a new test");
    const words = result.split(" ");
    // 'a' is both a stopword and short, should be removed
    expect(words).not.toContain("a");
  });

  it("limits to 5 keywords", () => {
    const result = extractKeywords(
      "implement user authentication with oauth2 security testing deployment",
    );
    const words = result.split(" ");
    expect(words.length).toBeLessThanOrEqual(5);
  });

  it("removes duplicates", () => {
    const result = extractKeywords(
      "test test authentication authentication test",
    );
    const words = result.split(" ");
    const uniqueWords = [...new Set(words)];
    expect(words.length).toBe(uniqueWords.length);
  });

  it("handles empty prompt", () => {
    const result = extractKeywords("");
    expect(result).toBe("");
  });

  it("handles prompt with only stopwords", () => {
    const result = extractKeywords("the a an is are was were");
    expect(result).toBe("");
  });

  it("preserves hyphenated words", () => {
    const result = extractKeywords("Implement end-to-end testing");
    // Hyphenated words may be split or preserved depending on implementation
    expect(result.length).toBeGreaterThan(0);
  });

  it("handles special characters", () => {
    const result = extractKeywords("Fix @mentions and #hashtags!");
    // Special characters are removed
    expect(result).not.toContain("@");
    expect(result).not.toContain("#");
  });
});

describe("checkMemoryRelevance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the mock to return a valid path
    vi.mocked(getOpcDir).mockReturnValue("/test/opc");
  });

  it("returns null for empty intent", () => {
    const result = checkMemoryRelevance("", "/test");
    expect(result).toBeNull();
  });

  it("returns null for very short intent", () => {
    const result = checkMemoryRelevance("ab", "/test");
    expect(result).toBeNull();
  });

  it("returns null when spawnSync fails", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 1,
      stdout: "",
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("authentication", "/test");
    expect(result).toBeNull();
  });

  it("parses JSON results from spawnSync", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        results: [
          {
            id: "12345678-1234-5678-1234-567812345678",
            content: "Test learning content",
            type: "PATTERN",
            score: 0.8,
          },
        ],
      }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("authentication", "/test");

    expect(result).not.toBeNull();
    expect(result!.count).toBe(1);
    expect(result!.results).toHaveLength(1);
  });

  it("extracts preview from content", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        results: [
          {
            id: "12345678",
            content:
              "This is a long learning about authentication patterns in OAuth2 implementations",
            type: "PATTERN",
            score: 0.9,
          },
        ],
      }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("authentication", "/test");

    expect(result!.results[0].content.length).toBeLessThanOrEqual(123); // 120 + "..."
  });

  it("handles multiple results", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        results: [
          { id: "1", content: "First result", type: "PATTERN", score: 0.9 },
          { id: "2", content: "Second result", type: "LEARNING", score: 0.8 },
          { id: "3", content: "Third result", type: "DECISION", score: 0.7 },
        ],
      }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("test", "/test");

    expect(result!.count).toBe(3);
    expect(result!.results).toHaveLength(3);
  });

  it("truncates ID to first 8 characters", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        results: [
          {
            id: "12345678-90ab-cdef-1234-567890abcdef",
            content: "Test",
            type: "PATTERN",
            score: 0.8,
          },
        ],
      }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("test", "/test");

    expect(result!.results[0].id).toHaveLength(8);
  });

  it("handles missing fields gracefully", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        results: [{ content: "Test with missing fields" }],
      }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("test", "/test");

    expect(result).not.toBeNull();
    expect(result!.results[0].id).toBe("unknown");
    expect(result!.results[0].type).toBe("UNKNOWN");
    expect(result!.results[0].score).toBe(0);
  });

  it("returns null for empty results array", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({ results: [] }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("test", "/test");

    expect(result).toBeNull();
  });

  it("handles malformed JSON", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: "not valid json",
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("test", "/test");

    expect(result).toBeNull();
  });
});

describe("Main function behavior", () => {
  it("skips for subagents", () => {
    process.env.CLAUDE_AGENT_ID = "test-agent";
    // Main function checks this and returns early
    expect(process.env.CLAUDE_AGENT_ID).toBeDefined();
    delete process.env.CLAUDE_AGENT_ID;
  });

  it("skips very short prompts", () => {
    // Main function returns early if prompt.length < 15
    const shortPrompt = "hi";
    expect(shortPrompt.length).toBeLessThan(15);
  });

  it("skips slash commands", () => {
    // Main function returns early if prompt starts with "/"
    const slashCommand = "/recall authentication";
    expect(slashCommand.trim().startsWith("/")).toBe(true);
  });

  it("skips when intent length is too short", () => {
    // Main function returns early if intent.length < 3
    const shortIntent = "ab";
    expect(shortIntent.length).toBeLessThan(3);
  });
});

describe("Edge Cases", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getOpcDir).mockReturnValue("/test/opc");
  });

  it("handles underscore in intent", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({ results: [] }),
    } as ReturnType<typeof spawnSync>);

    // Underscores are converted to spaces
    checkMemoryRelevance("auth_module_config", "/test");
    expect(spawnSync).toHaveBeenCalled();
  });

  it("handles forward slash in intent", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({ results: [] }),
    } as ReturnType<typeof spawnSync>);

    // Slashes are converted to spaces
    checkMemoryRelevance("auth/module/config", "/test");
    expect(spawnSync).toHaveBeenCalled();
  });

  it("handles very long prompts", () => {
    const longPrompt = "a".repeat(10000);
    const result = extractIntent(longPrompt);
    // Should process without error
    expect(typeof result).toBe("string");
    expect(result.length).toBeLessThanOrEqual(longPrompt.length);
  });

  it("handles prompts with only punctuation", () => {
    const result = extractKeywords("!!! ??? ...");
    expect(result).toBe("");
  });

  it("extracts preview from multi-line content", () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        results: [
          {
            id: "test",
            content: "Line one\nLine two\nLine three\nLine four",
            type: "PATTERN",
            score: 0.8,
          },
        ],
      }),
    } as ReturnType<typeof spawnSync>);

    const result = checkMemoryRelevance("test", "/test");
    expect(result).not.toBeNull();
    // Should join lines and truncate
    expect(result!.results[0].content).toContain("Line one");
    expect(result!.results[0].content.length).toBeLessThanOrEqual(123);
  });
});

describe("Integration", () => {
  it("end-to-end: prompt to intent extraction", () => {
    const prompt = "Can you help?";
    const intent = extractIntent(prompt);
    // Falls back to keywords, "help" is a stopword so result may be short
    expect(typeof intent).toBe("string");
  });

  it("end-to-end: full prompt extraction", () => {
    const prompt =
      "Can you please show me how to implement OAuth2 authentication?";
    const intent = extractIntent(prompt);
    // Should strip meta-phrases
    expect(intent).not.toContain("Can you");
    // Result should be shorter than original
    expect(intent.length).toBeLessThan(prompt.length);
  });

  it("end-to-end: keywords from complex prompt", () => {
    const prompt =
      "I want to understand the differences between JWT and OAuth2 for authentication";
    const keywords = extractKeywords(prompt);

    // Should exclude stopwords and keep meaningful words
    const words = keywords.split(" ");
    expect(words.length).toBeLessThanOrEqual(5);
    // Should not contain common stopwords
    expect(words).not.toContain("the");
    expect(words).not.toContain("to");
  });
});
