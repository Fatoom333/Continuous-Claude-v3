---
name: continuity
description: "Problem-solving strategies for continuity in real analysis"
allowed-tools: [Bash, Read]
---

# Continuity

## When to Use

Use this skill when working on continuity problems in real analysis.

## Decision Tree

1. **Check Definition**
   - f(a) exists (function defined at point)
   - lim\_{x->a} f(x) exists
   - lim\_{x->a} f(x) = f(a)

2. **Use SymPy for Limit Check**
   - `sympy_compute.py limit "<f>" --var x --to <a>`
   - Compare with f(a)

3. **Piecewise Functions**
   - Check left and right limits separately
   - `sympy_compute.py limit "<f>" --var x --to <a> --dir -` (use `--dir +` for the right limit)

4. **Verify with Z3**
   - Check a concrete epsilon-delta choice: `z3_solve.py prove "<f_close_to_L>" --assume <delta_condition> --type real`

## Tool Commands

### Sympy_Limit

```bash
# Removable discontinuity: limit is 1, so define f(0) = 1
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "sin(x)/x" --var x --to 0
```

### Sympy_One_Sided_Limits

```bash
# Jump discontinuity of |x|/x at 0: left -1, right 1
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "abs(x)/x" --var x --to 0 --dir -
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "abs(x)/x" --var x --to 0 --dir +
```

### Z3_Epsilon_Delta

```bash
# f(x) = 2x + 1 is continuous at 1 with delta = epsilon/2
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "-e < (2*x + 1) - 3 < e" --assume "e > 0" "d == e/2" "-d < x - 1 < d" --type real
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
