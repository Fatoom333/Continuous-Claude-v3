---
name: convergence
description: "Problem-solving strategies for convergence in real analysis"
allowed-tools: [Bash, Read]
---

# Convergence

## When to Use

Use this skill when working on convergence problems in real analysis.

## Decision Tree

1. **Identify Sequence/Series Type**
   - Geometric series: |r| < 1 converges
   - p-series: p > 1 converges
   - Alternating series: check decreasing + limit 0

2. **Apply Convergence Tests**
   - Ratio test: `sympy_compute.py limit "<a_next>/<a_n>" --var n --to oo` (converges if < 1)
   - Root test: `sympy_compute.py limit "<a_n>**(1/n)" --var n --to oo`
   - Comparison test: find bounding series

3. **Verify Bounds**
   - Prove comparison bounds: `z3_solve.py prove "<inequality>" --assume "n >= 1" --type real`
   - Check monotonicity with derivatives

4. **Compute Sum (if convergent)**
   - `sympy_compute.py sum "<a_n>" --var n --from <start> --to oo` (also reports convergence)

## Tool Commands

### Sympy_Ratio_Test

```bash
# a_n = n / 2^n: ratio tends to 1/2 < 1, so the series converges
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "((n+1)/2**(n+1)) / (n/2**n)" --var n --to oo
```

### Sympy_Sum

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" sum "1/n**2" --var n --from 1 --to oo
```

### Z3_Comparison_Bound

```bash
# 1/(n^2 + n) <= 1/n^2, so sum 1/(n^2 + n) converges by comparison with sum 1/n^2
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "1/(n*n + n) <= 1/(n*n)" --assume "n >= 1" --type real
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
