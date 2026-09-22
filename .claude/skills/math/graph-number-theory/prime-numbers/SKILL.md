---
name: prime-numbers
description: "Problem-solving strategies for prime numbers in graph number theory"
allowed-tools: [Bash, Read]
---

# Prime Numbers

## When to Use

Use this skill when working on prime-numbers problems in graph number theory.

## Decision Tree

1. **Primality testing hierarchy**
   - Trial division: O(sqrt(n)), exact
   - Miller-Rabin: O(k log^3 n), probabilistic
   - AKS: O(log^6 n), deterministic polynomial

2. **Factorization**
   - Trial division for small factors
   - Pollard's rho: probabilistic, medium numbers
   - Quadratic sieve: large numbers
   - `sympy_compute.py factorint <n>`

3. **Prime distribution**
   - Prime Number Theorem: pi(x) ~ x/ln(x)
   - Prime gaps: p\_{n+1} - p_n
   - Check numerically: `mpmath_compute.py mp_primepi <x>` against x/ln(x)

4. **Fermat's Little Theorem**
   - a^{p-1} = 1 (mod p) for a not divisible by p
   - Use for modular exponentiation
   - For a fixed p: `z3_solve.py prove "(a**<p_minus_1>) % <p> == 1" --assume "1 <= a <= <p_minus_1>"`

5. **Wilson's Theorem**
   - (p-1)! = -1 (mod p) iff p is prime

## Tool Commands

### Sympy_Factor

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" factorint 360
```

### Sympy_Isprime

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" isprime 1000003
```

### Mpmath_Prime_Count

```bash
# pi(1000) = 168, while 1000/ln(1000) is about 145
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/mpmath_compute.py" mp_primepi 1000
```

### Z3_Fermat_Little

```bash
# a^6 = 1 (mod 7) for every a in 1..6
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "(a**6) % 7 == 1" --assume "1 <= a <= 6"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
