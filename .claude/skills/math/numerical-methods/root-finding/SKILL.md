---
name: root-finding
description: "Problem-solving strategies for root finding in numerical methods"
allowed-tools: [Bash, Read]
---

# Root Finding

## When to Use

Use this skill when working on root-finding problems in numerical methods.

## Decision Tree

1. **Characterize the Problem**
   - Single root or multiple roots?
   - Bracketed (know interval containing root)?
   - Derivatives available?

2. **Method Selection**
   | Situation | Method | Implementation |
   |-----------|--------|----------------|
   | Bracketed, no derivatives | Bisection, Brent | `scipy.optimize.brentq` |
   | Derivatives available | Newton-Raphson | `scipy.optimize.newton` |
   | No derivatives | Secant method | `scipy.optimize.newton` (no fprime) |
   | System of equations | `scipy.optimize.fsolve` | Requires Jacobian ideally |

3. **Implement Root Finding**
   - `scipy.optimize.brentq(f, a, b)` - guaranteed convergence if bracketed
   - `scipy.optimize.newton(f, x0, fprime=df)` - quadratic convergence near root
   - For systems: `scipy.optimize.fsolve(F, x0)`

4. **Handle Multiple Roots**
   - Deflation: divide out found roots
   - Multiple starting points
   - `sympy_compute.py solve "f(x)" --var x` for symbolic solutions

5. **Verify Solutions**
   - Check |f(root)| < tolerance
   - Verify root is in expected domain
   - `z3_solve.py prove "f(root) == 0"`

## Tool Commands

### Scipy_Brentq

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import brentq; root = brentq(lambda x: x**2 - 2, 0, 2); print('Root:', root)"
```

### Scipy_Newton

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import newton; root = newton(lambda x: x**2 - 2, 1.0, fprime=lambda x: 2*x); print('Root:', root)"
```

### Sympy_Solve

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "x**3 - x - 1" --var x
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
