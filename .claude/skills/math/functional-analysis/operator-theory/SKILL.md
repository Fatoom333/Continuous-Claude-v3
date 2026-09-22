---
name: operator-theory
description: "Problem-solving strategies for operator theory in functional analysis"
allowed-tools: [Bash, Read]
---

# Operator Theory

## When to Use

Use this skill when working on operator-theory problems in functional analysis.

## Decision Tree

1. **Bounded operator verification**
   - ||Tx|| <= M||x|| for some M
   - Operator norm: ||T|| = sup{||Tx|| : ||x|| = 1}
   - `z3_solve.py prove "operator_bounded"`

2. **Adjoint operator**
   - <Tx, y> = <x, T*y> defines T*
   - For matrices: T\* = conjugate transpose
   - `sympy_compute.py simplify "<Tx, y> - <x, T*y>"`

3. **Spectral Theory**
   - Spectrum: sigma(T) = {lambda : T - lambda\*I not invertible}
   - Self-adjoint: spectrum is real
   - `z3_solve.py prove "self_adjoint_real_spectrum"`

4. **Compact operators**
   - T compact if T(bounded set) has compact closure
   - Approximable by finite-rank operators
   - `sympy_compute.py limit "||T - T_n||" --var n`

5. **Spectral Theorem**
   - Self-adjoint compact: T = sum(lambda_n \* P_n)
   - eigenvalues -> 0, eigenvectors form orthonormal basis

## Tool Commands

### Z3_Bounded_Operator

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "norm(Tx) <= M*norm(x)"
```

### Sympy_Adjoint

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "<Tx, y> - <x, T_star_y>"
```

### Z3_Spectral

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "self_adjoint implies real_spectrum"
```

### Sympy_Compact

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "norm(T - T_n)" --var n --at oo
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
