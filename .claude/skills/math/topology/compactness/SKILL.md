---
name: compactness
description: "Problem-solving strategies for compactness in topology"
allowed-tools: [Bash, Read]
---

# Compactness

## When to Use

Use this skill when working on compactness problems in topology.

## Decision Tree

1. **Is X compact?**
   - If X subset R^n: Is X closed AND bounded? (Heine-Borel)
   - If X is metric: Does every sequence have convergent subsequence?
   - General: Does every open cover have finite subcover?
   - `z3_solve.py prove "bounded_and_closed"`

2. **Compactness Tests**
   - Heine-Borel (R^n): closed + bounded = compact
   - Sequential: every sequence has convergent subsequence
   - `sympy_compute.py limit "a_n" --var n` to check convergence

3. **Product Spaces**
   - Tychonoff: product of compact spaces is compact
   - Finite products preserve compactness directly

4. **Consequences of Compactness**
   - Continuous image of compact is compact
   - Continuous real function on compact attains max/min
   - `sympy_compute.py maximum "f(x)" --var x --domain "[a,b]"`

## Tool Commands

### Z3_Bounded_Closed

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "bounded_and_closed"
```

### Sympy_Limit

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "a_n" --var n --at oo
```

### Sympy_Maximum

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" maximum "f(x)" --var x --domain "[a,b]"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
