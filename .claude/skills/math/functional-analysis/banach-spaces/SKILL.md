---
name: banach-spaces
description: "Problem-solving strategies for banach spaces in functional analysis"
allowed-tools: [Bash, Read]
---

# Banach Spaces

## When to Use

Use this skill when working on banach-spaces problems in functional analysis.

## Decision Tree

1. **Verify Banach space**
   - Complete normed vector space
   - Check: every Cauchy sequence converges
   - `z3_solve.py prove "completeness"`

2. **Hahn-Banach Theorem**
   - Extend bounded linear functionals
   - Separate convex sets
   - `z3_solve.py prove "extension_exists"`

3. **Open Mapping Theorem**
   - Surjective bounded operator between Banach spaces is open
   - Consequence: bounded inverse exists
   - `z3_solve.py prove "open_mapping"`

4. **Closed Graph Theorem**
   - T: X -> Y has closed graph implies T bounded
   - Strategy: verify graph closure, conclude boundedness
   - `z3_solve.py prove "closed_graph_implies_bounded"`

5. **Uniform Boundedness Principle**
   - Pointwise bounded family of operators is uniformly bounded
   - Application: prove operator families are bounded

## Tool Commands

### Z3_Completeness

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "cauchy_sequence implies convergent"
```

### Z3_Open_Mapping

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "T_surjective_bounded implies T_open"
```

### Z3_Closed_Graph

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "graph_closed implies T_bounded"
```

### Sympy_Norm

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "norm(alpha*x + beta*y)"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
