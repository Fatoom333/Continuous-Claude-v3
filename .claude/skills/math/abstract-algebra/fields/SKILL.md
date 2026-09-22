---
name: fields
description: "Problem-solving strategies for fields in abstract algebra"
allowed-tools: [Bash, Read]
---

# Fields

## When to Use

Use this skill when working on fields problems in abstract algebra.

## Decision Tree

1. **Is F a field?**
   - (F, +) is an abelian group with identity 0
   - (F \ {0}, \*) is an abelian group with identity 1
   - Distributive law holds
   - For Z_n: a field iff there are no zero divisors; search with `z3_solve.py sat "(a*b) % <n> == 0, 1 <= a < <n>, 1 <= b < <n>"`

2. **Field Extensions**
   - E is extension of F if F is subfield of E
   - Degree [E:F] = dimension of E as F-vector space
   - `sympy_compute.py minpoly "<alpha>" --var x` for minimal polynomial

3. **Characteristic**
   - char(F) = smallest n > 0 where n\*1 = 0, or 0 if none exists
   - char(F) is 0 or prime
   - For finite field: |F| = p^n where p = char(F)

4. **Algebraic Elements**
   - alpha is algebraic over F if it satisfies polynomial with coefficients in F
   - `sympy_compute.py solve "<polynomial>" --var x` for algebraic relations

## Tool Commands

### Z3_Zero_Divisors

```bash
# Z_6 is not a field: 2 * 3 = 0 (mod 6)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" sat "(a*b) % 6 == 0, 1 <= a < 6, 1 <= b < 6"
# Z_7 has no zero divisors (7 is prime)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "(a*b) % 7 != 0" --assume "1 <= a < 7" "1 <= b < 7"
```

### Sympy_Minpoly

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" minpoly "sqrt(2)" --var x
# Degree 4 = [Q(sqrt 2, sqrt 3) : Q]
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" minpoly "sqrt(2) + sqrt(3)" --var x
```

### Sympy_Solve

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "x**2 - 2" --var x
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
