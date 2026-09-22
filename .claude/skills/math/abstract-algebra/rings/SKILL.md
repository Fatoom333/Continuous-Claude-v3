---
name: rings
description: "Problem-solving strategies for rings in abstract algebra"
allowed-tools: [Bash, Read]
---

# Rings

## When to Use

Use this skill when working on rings problems in abstract algebra.

## Decision Tree

1. **Is R a ring?**
   - (R, +) is an abelian group
   - Multiplication is associative
   - Distributive laws: a(b+c) = ab + ac and (a+b)c = ac + bc
   - Check each law with `z3_solve.py prove "<law>" --assume <domain_conditions>`

2. **Ring Properties**
   - Commutative ring: ab = ba for all a, b?
   - Ring with unity: exists 1 such that 1*a = a*1 = a?
   - Integral domain: ab = 0 implies a = 0 or b = 0?
   - Zero divisors in Z_n: `z3_solve.py sat "(a*b) % <n> == 0, 0 < a < <n>, 0 < b < <n>"`

3. **Ideals**
   - I is ideal if: I is additive subgroup AND for all r in R, a in I: ra in I, ar in I
   - Principal ideal: (a) = {ra : r in R}
   - In F[x] every ideal is principal: (p, q) = (gcd(p, q)), via `sympy_compute.py gcd "<p>" "<q>"`

4. **Ring Homomorphisms**
   - phi(a + b) = phi(a) + phi(b)
   - phi(ab) = phi(a)phi(b)
   - phi(1) = 1 (for rings with unity)

## Tool Commands

### Z3_Ring_Axioms

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "ForAll([a,b,c], a*(b+c) == a*b + a*c)"
```

### Z3_Integral_Domain

```bash
# Z is an integral domain
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "Implies(a*b == 0, Or(a == 0, b == 0))"
```

### Sympy_Ideal

```bash
# (x^2 - 1, x^2 - 2x + 1) = (x - 1) in Q[x]
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" gcd "x**2 - 1" "x**2 - 2*x + 1"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
