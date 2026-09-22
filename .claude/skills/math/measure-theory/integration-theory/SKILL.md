---
name: integration-theory
description: "Problem-solving strategies for integration theory in measure theory"
allowed-tools: [Bash, Read]
---

# Integration Theory

## When to Use

Use this skill when working on integration-theory problems in measure theory.

## Decision Tree

1. **Simple function integration**
   - For s = sum(a*i \* chi*{E_i}): integral s dmu = sum(a_i \* mu(E_i))
   - `sympy_compute.py simplify "simple_integral"`

2. **Monotone Convergence Theorem (MCT)**
   - If 0 <= f*n <= f*{n+1} and f_n -> f:
   - lim integral(f_n) = integral(lim f_n)
   - Use for increasing sequences

3. **Dominated Convergence Theorem (DCT)**
   - If |f_n| <= g (integrable) and f_n -> f pointwise:
   - lim integral(f_n) = integral(f)
   - `z3_solve.py prove "dominated_convergence"`

4. **Fatou's Lemma**
   - integral(liminf f_n) <= liminf(integral f_n)
   - Use as lower bound when MCT/DCT don't apply

5. **Fubini-Tonelli**
   - For product measures: switch order of integration
   - Tonelli: non-negative functions (always valid)
   - Fubini: integrable functions

## Tool Commands

### Sympy_Simple_Integral

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" integrate "sum(a_i * chi_E_i)" --var mu
```

### Z3_Mct

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "f_n_increasing implies lim_integral_equals_integral_lim"
```

### Z3_Dct

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "abs(f_n) <= g and g_integrable implies limit_exchange"
```

### Sympy_Fatou

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "liminf(integral_f_n)" --comparison "integral_liminf_f_n"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
