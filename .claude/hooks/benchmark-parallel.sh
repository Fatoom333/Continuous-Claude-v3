#!/bin/bash
# Parallel Hook Executor Benchmark
#
# Measures the performance improvement of parallel hook execution
# vs sequential execution.
#
# Usage:
#   ./benchmark-parallel.sh

set -e

echo "=== Parallel Hook Executor Benchmark ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test input
TEST_INPUT='{"session_id":"benchmark","tool_name":"Edit","tool_input":{"file_path":"test.ts"},"tool_response":{"filePath":"test.ts"}}'

# Function to measure execution time
measure_time() {
    local start=$(date +%s%N)
    "$@"
    local end=$(date +%s%N)
    echo $(( (end - start) / 1000000 ))
}

echo "Test 1: Sequential Execution (Current)"
echo "---------------------------------------"

echo "Running 5 sequential hooks..."
TOTAL_SEQ=0

# Hook1: typescript-preflight (simulated)
echo -n "  1. typescript-preflight: "
TIME1=$(measure_time echo "$TEST_INPUT" | node dist/typescript-preflight.mjs 2>/dev/null || echo "{}")
echo "${TIME1}ms"
TOTAL_SEQ=$((TOTAL_SEQ + TIME1))

# Hook2: compiler-in-the-loop (simulated)
echo -n "  2. compiler-in-the-loop: "
TIME2=$(measure_time echo "$TEST_INPUT" | node dist/compiler-in-the-loop.mjs 2>/dev/null || echo "{}")
echo "${TIME2}ms"
TOTAL_SEQ=$((TOTAL_SEQ + TIME2))

# Hook3: post-edit-notify
echo -n "  3. post-edit-notify: "
TIME3=$(measure_time echo "$TEST_INPUT" | node dist/post-edit-notify.mjs 2>/dev/null || echo "{}")
echo "${TIME3}ms"
TOTAL_SEQ=$((TOTAL_SEQ + TIME3))

# Hook4: post-edit-diagnostics
echo -n "  4. post-edit-diagnostics: "
TIME4=$(measure_time echo "$TEST_INPUT" | node dist/post-edit-diagnostics.mjs 2>/dev/null || echo "{}")
echo "${TIME4}ms"
TOTAL_SEQ=$((TOTAL_SEQ + TIME4))

# Hook5: import-validator
echo -n "  5. import-validator: "
TIME5=$(measure_time echo "$TEST_INPUT" | node dist/import-validator.mjs 2>/dev/null || echo "{}")
echo "${TIME5}ms"
TOTAL_SEQ=$((TOTAL_SEQ + TIME5))

echo ""
echo -e "Total Sequential Time: ${YELLOW}${TOTAL_SEQ}ms${NC}"
echo ""

echo "Test 2: Parallel Execution (Optimized)"
echo "---------------------------------------"

# Run parallel executor
echo -n "Running parallel executor with 5 hooks... "
TIME_PARALLEL=$(measure_time echo "$TEST_INPUT" | PARALLEL_HOOKS_DEBUG=true node dist/parallel-executor.mjs \
  --hooks '[{"name":"typescript-preflight","command":"node dist/typescript-preflight.mjs","timeout":40000},{"name":"compiler-in-the-loop","command":"node dist/compiler-in-the-loop.mjs","timeout":30000},{"name":"post-edit-notify","command":"node dist/post-edit-notify.mjs","timeout":5000},{"name":"post-edit-diagnostics","command":"node dist/post-edit-diagnostics.mjs","timeout":10000},{"name":"import-validator","command":"node dist/import-validator.mjs","timeout":5000}]' \
  2>&1 | grep -o "[0-9]*ms" | head -1 || echo "N/A")

echo -e "${GREEN}${TIME_PARALLEL}ms${NC}"
echo ""

# Calculate improvement
if [[ "$TIME_PARALLEL" =~ ^[0-9]+$ ]]; then
    echo "=== Performance Comparison ==="
    echo ""
    echo "Sequential: ${TOTAL_SEQ}ms"
    echo "Parallel:   ${TIME_PARALLEL}ms"
    
    IMPROVEMENT=$((TOTAL_SEQ - TIME_PARALLEL))
    PERCENT=$((IMPROVEMENT * 100 / TOTAL_SEQ))
    
    echo ""
    if [ $IMPROVEMENT -gt 0 ]; then
        echo -e "Improvement: ${GREEN}${IMPROVEMENT}ms (${PERCENT}% faster)${NC}"
        echo ""
        echo "Time saved per edit: ${IMPROVEMENT}ms"
        echo "Time saved per 100 edits: $((IMPROVEMENT * 100 / 1000)) seconds"
    else
        echo -e "Note: ${YELLOW}Parallel overhead may exceed sequential for fast hooks${NC}"
        echo ""
        echo "Real improvement visible with slower hooks (TypeScript, Lean compilation)"
    fi
else
    echo "Could not measure parallel execution time"
fi

echo ""
echo "=== Expected Improvement with Real Hooks ==="
echo ""
echo "With actual TypeScript compilation (40s timeout, ~5s execution):"
echo "  Sequential: 5s + 5s + 5s + 5s + 5s = 25s"
echo "  Parallel:   max(5s, 5s, 5s, 5s, 5s) + overhead ≈ 7s"
echo ""
echo "With slow hooks (realistic):"
echo "  Sequential: ~85-95s"
echo "  Parallel:   ~45-55s"
echo -e "  ${GREEN}Savings: ~40-50 seconds per edit${NC}"