---
name: limits
description: "Problem-solving strategies for limits in real analysis"
allowed-tools: [Bash, Read]
---

# Limits

## When to Use

Use this skill when working on limits problems in real analysis.

## Decision Tree

1. **Direct Substitution**
   - Try plugging in the value directly
   - If you get a determinate form, that's the answer

2. **Indeterminate Form? (0/0, inf/inf)**
   - Try algebraic manipulation (factor, rationalize)
   - Try L'Hopital's rule: `sympy_compute.py diff "<numerator>" --var x` and the same for the denominator

3. **Squeeze Theorem**
   - If bounded: find g(x) <= f(x) <= h(x) where lim g = lim h
   - Verify bounds with `z3_solve.py prove`

4. **Epsilon-Delta Proof**
   - For rigorous proof: set up |f(x) - L| < epsilon
   - Find delta in terms of epsilon
   - Verify with `math_scratchpad.py verify`

## Tool Commands

### Sympy_Limit

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "sin(x)/x" --var x --to 0
```

### Sympy_Diff

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" diff "x**2" --var x
```

### Z3_Squeeze_Bound

```bash
# -x^2 <= x^2 sin(1/x) <= x^2 with s = sin(1/x) in [-1, 1], so the limit at 0 is 0
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "-x*x <= x*x*s <= x*x" --assume "-1 <= s <= 1" --type real
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
