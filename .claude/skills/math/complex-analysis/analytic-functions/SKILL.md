---
name: analytic-functions
description: "Problem-solving strategies for analytic functions in complex analysis"
allowed-tools: [Bash, Read]
---

# Analytic Functions

## When to Use

Use this skill when working on analytic-functions problems in complex analysis.

## Decision Tree

1. **Is f analytic at z0?**
   - Check Cauchy-Riemann equations: du/dx = dv/dy, du/dy = -dv/dx
   - Check if f has power series expansion around z0
   - Check if f is differentiable in neighborhood of z0
   - `sympy_compute.py diff "<u>" --var x` and `sympy_compute.py diff "<v>" --var y`

2. **Cauchy-Riemann Verification**
   - Write f(z) = u(x,y) + iv(x,y)
   - Compute partial derivatives
   - Verify: du/dx = dv/dy AND du/dy = -dv/dx
   - Both differences must simplify to 0: `sympy_compute.py simplify "diff(<u>, x) - diff(<v>, y)"`

3. **Power Series**
   - f(z) = sum\_{n=0}^{inf} a_n (z - z0)^n
   - Radius of convergence: R = 1/limsup |a_n|^(1/n)
   - `sympy_compute.py series "<f>" --var z --point <z0>`

4. **Analytic Continuation**
   - Extend f beyond original domain via power series
   - Identity theorem: if f = g on set with limit point, then f = g everywhere

## Tool Commands

### Sympy_Diff_U

```bash
# f(z) = z^2: u = x^2 - y^2, v = 2xy
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" diff "x**2 - y**2" --var x
```

### Sympy_Diff_V

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" diff "2*x*y" --var y
```

### Sympy_Series

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" series "exp(z)" --var z --point 0
```

### Sympy_Cauchy_Riemann

```bash
# u_x - v_y = 0 and u_y + v_x = 0, so z^2 satisfies Cauchy-Riemann everywhere
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "diff(x**2 - y**2, x) - diff(2*x*y, y)"
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "diff(x**2 - y**2, y) + diff(2*x*y, x)"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
