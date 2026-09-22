---
name: open-sets
description: "Problem-solving strategies for open sets in topology"
allowed-tools: [Bash, Read]
---

# Open Sets

## When to Use

Use this skill when working on open-sets problems in topology.

## Decision Tree

1. **Is f: X -> Y continuous?**
   - For metric spaces: x_n -> x implies f(x_n) -> f(x)?
   - For general spaces: f^(-1)(open) = open?
   - For products: Check each coordinate function
   - `z3_solve.py prove "preimage_open"`

2. **Open Set Verification**
   - For metric spaces: for all x in U, exists epsilon > 0 with B(x,epsilon) subset U
   - `z3_solve.py prove "ball_contained"` with epsilon witnesses

3. **Topological Properties**
   - Interior: int(A) = largest open subset of A
   - Closure: cl(A) = smallest closed superset of A
   - Boundary: bd(A) = cl(A) \ int(A)

4. **Continuity Tests**
   - Epsilon-delta: for all epsilon > 0, exists delta > 0: d(x,a) < delta implies d(f(x),f(a)) < epsilon
   - `z3_solve.py prove "epsilon_delta_bound"`

## Tool Commands

### Z3_Preimage_Open

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "preimage_open"
```

### Z3_Epsilon_Delta

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "ForAll(eps, Exists(delta, d(x,a) < delta implies d(f(x),f(a)) < eps))"
```

### Z3_Ball_Contained

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "ball_contained"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
