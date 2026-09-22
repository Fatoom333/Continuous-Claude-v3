---
name: modular-arithmetic
description: "Problem-solving strategies for modular arithmetic in graph number theory"
allowed-tools: [Bash, Read]
---

# Modular Arithmetic

## When to Use

Use this skill when working on modular-arithmetic problems in graph number theory.

## Decision Tree

1. **Extended Euclidean Algorithm**
   - Find gcd(a,b) and x,y with ax + by = gcd(a,b)
   - Modular inverse: a^{-1} mod n when gcd(a,n) = 1
   - `sympy_compute.py modinverse <a> <n>`

2. **Chinese Remainder Theorem**
   - System x = a_i (mod m_i) with coprime m_i
   - Unique solution mod prod(m_i)
   - `z3_solve.py sat "x % <m1> == <a1>, x % <m2> == <a2>, 0 <= x < <m1_times_m2>"`

3. **Euler's Theorem**
   - a^{phi(n)} = 1 (mod n) when gcd(a,n) = 1
   - phi(p^k) = p^{k-1}(p-1)
   - Factor n with `sympy_compute.py factorint <n>`, then phi(n) = n * prod(1 - 1/p)

4. **Quadratic Residues**
   - Legendre symbol: (a/p) = a^{(p-1)/2} mod p
   - Quadratic reciprocity: (p/q)(q/p) = (-1)^{...}
   - Tonelli-Shanks for square roots

5. **Order and Primitive Roots**
   - ord_n(a) = smallest k with a^k = 1 (mod n)
   - Primitive root: ord_n(a) = phi(n)

## Tool Commands

### Sympy_Mod_Inverse

```bash
# 3 * 4 = 12 = 1 (mod 11)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" modinverse 3 11
```

### Z3_Crt

```bash
# x = 2 (mod 3), x = 3 (mod 5), x = 2 (mod 7): unique x = 23 mod 105
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" sat "x % 3 == 2, x % 5 == 3, x % 7 == 2, 0 <= x < 105"
```

### Sympy_Euler_Phi

```bash
# 360 = 2^3 * 3^2 * 5, so phi(360) = 360 * 1/2 * 2/3 * 4/5 = 96
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" factorint 360
```

### Z3_Quadratic_Residue

```bash
# Is 5 a quadratic residue mod 11? A model x means x^2 = 5 (mod 11)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" sat "x*x % 11 == 5, 0 <= x < 11"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
