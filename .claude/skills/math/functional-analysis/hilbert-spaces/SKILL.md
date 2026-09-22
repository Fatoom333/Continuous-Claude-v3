---
name: hilbert-spaces
description: "Problem-solving strategies for hilbert spaces in functional analysis"
allowed-tools: [Bash, Read]
---

# Hilbert Spaces

## When to Use

Use this skill when working on hilbert-spaces problems in functional analysis.

## Decision Tree

1. **Orthogonal decomposition**
   - For closed subspace M: H = M + M^perp (direct sum)
   - Every x = P*M(x) + P*{M^perp}(x)
   - `sympy_compute.py simplify "x - projection"`

2. **Projection Theorem**
   - For closed convex C, unique nearest point exists
   - P_C is nonexpansive: ||P_C(x) - P_C(y)|| <= ||x - y||
   - `z3_solve.py prove "projection_exists_unique"`

3. **Riesz Representation**
   - Every f in H\* has form f(x) = <x, y_f> for unique y_f
   - ||f|| = ||y_f||
   - `z3_solve.py prove "riesz_representation"`

4. **Parseval's Identity**
   - For orthonormal basis {e_n}: ||x||^2 = sum|<x, e_n>|^2
   - `sympy_compute.py sum "abs(<x, e_n>)**2"`

5. **Bessel's Inequality**
   - sum|<x, e_n>|^2 <= ||x||^2 for any orthonormal set

## Tool Commands

### Sympy_Inner_Product

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "<x + y, z> == <x,z> + <y,z>"
```

### Z3_Projection

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "x - P_M(x) in M_perp"
```

### Z3_Riesz

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "bounded_linear_functional iff inner_product_form"
```

### Sympy_Parseval

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" sum "abs(<x, e_n>)**2" --var n --from 1 --to oo
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
