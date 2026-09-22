---
name: connectedness
description: "Problem-solving strategies for connectedness in topology"
allowed-tools: [Bash, Read]
---

# Connectedness

## When to Use

Use this skill when working on connectedness problems in topology.

## Decision Tree

1. **Is X connected?**
   - Strategy 1 - Contradiction:
     - Assume X = U union V where U, V are disjoint, non-empty, and open
     - Derive a contradiction
   - Strategy 2 - Path connectedness:
     - Show for all x,y in X, exists continuous path f: [0,1] -> X with f(0)=x, f(1)=y
   - Strategy 3 - Fan lemma:
     - If {A_i} are connected sharing a common point, then union A_i is connected

2. **Connectedness Proofs**
   - Show no separation exists
   - `z3_solve.py prove "no_separation"`
   - Use intermediate value theorem for R subsets

3. **Path Connectedness**
   - Construct explicit path: f(t) = (1-t)x + ty for convex sets
   - `sympy_compute.py simplify "(1-t)*x + t*y"` to verify path

4. **Components**
   - Connected component: maximal connected subset containing x
   - Path component: maximal path-connected subset containing x

## Tool Commands

### Z3_No_Separation

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "no_separation"
```

### Sympy_Path

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "(1-t)*x + t*y"
```

### Z3_Ivt

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "intermediate_value"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
