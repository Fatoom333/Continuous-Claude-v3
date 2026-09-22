---
name: lebesgue-measure
description: "Problem-solving strategies for lebesgue measure in measure theory"
allowed-tools: [Bash, Read]
---

# Lebesgue Measure

## When to Use

Use this skill when working on lebesgue-measure problems in measure theory.

## Decision Tree

1. **Outer measure construction**
   - m\*(A) = inf{sum |I_n| : A subset union(I_n)}
   - `sympy_compute.py sum "length(I_n)" --var n`

2. **Caratheodory criterion**
   - E is measurable if: m*(A) = m*(A & E) + m\*(A & E^c) for all A
   - `z3_solve.py prove "caratheodory_criterion"`

3. **Lebesgue measure properties**
   - Translation invariant: m(E + x) = m(E)
   - sigma-additive on measurable sets
   - m([a,b]) = b - a

4. **Regularity theorems**
   - Inner regularity: m(E) = sup{m(K) : K compact, K subset E}
   - Outer regularity: m(E) = inf{m(U) : U open, E subset U}

## Tool Commands

### Sympy_Outer_Measure

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" sum "length(I_n)" --var n --from 1 --to oo
```

### Z3_Caratheodory

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "mu(A) == mu(A & E) + mu(A & E_complement)"
```

### Sympy_Borel_Sets

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "open_set_countable_union"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
