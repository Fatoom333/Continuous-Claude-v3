---
name: vector-spaces
description: "Problem-solving strategies for vector spaces in linear algebra"
allowed-tools: [Bash, Read]
---

# Vector Spaces

## When to Use

Use this skill when working on vector-spaces problems in linear algebra.

## Decision Tree

1. **Check Subspace**
   - Contains zero vector?
   - Closed under addition?
   - Closed under scalar multiplication?
   - Verify closure with `z3_solve.py prove "<closure_condition>" --assume <membership_conditions>`

2. **Linear Independence**
   - Set up Ax = 0 where columns are vectors
   - `sympy_compute.py nullspace "<matrix>"`
   - Trivial nullspace = independent

3. **Basis and Dimension**
   - Find spanning set, remove dependent vectors
   - `sympy_compute.py rref "<matrix>"` to find pivot columns
   - Dimension = number of pivots

4. **Change of Basis**
   - Find transition matrix P
   - New coords = P^(-1) \* old coords
   - `sympy_compute.py inverse "<transition_matrix>"`

## Tool Commands

### Sympy_Nullspace

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" nullspace "[[1,2,3],[4,5,6]]"
```

### Sympy_Rref

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" rref "[[1,2,3],[4,5,6]]"
```

### Z3_Subspace_Closure

```bash
# Plane x + y + z = 0 is closed under addition
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "(a1 + b1) + (a2 + b2) + (a3 + b3) == 0" --assume "a1 + a2 + a3 == 0" "b1 + b2 + b3 == 0"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
