---
name: numerical-integration
description: "Problem-solving strategies for numerical integration in numerical methods"
allowed-tools: [Bash, Read]
---

# Numerical Integration

## When to Use

Use this skill when working on numerical-integration problems in numerical methods.

## Decision Tree

1. **Identify Integral Type**
   - Definite integral over finite interval?
   - Improper integral (infinite bounds or singularities)?
   - Multiple dimensions?

2. **Select Quadrature Method**
   - Smooth function, finite interval: Gaussian quadrature
   - Oscillatory integrand: specialized methods (Filon, Levin)
   - Singularity at endpoint: adaptive methods
   - `scipy.integrate.quad(f, a, b)` for general 1D

3. **Adaptive Integration**
   - Let algorithm subdivide where needed
   - Specify error tolerances (rtol, atol)
   - `scipy.integrate.quad(f, a, b, epsabs=1e-8, epsrel=1e-8)`

4. **Multiple Dimensions**
   - `scipy.integrate.dblquad` for 2D
   - `scipy.integrate.tplquad` for 3D
   - Monte Carlo for higher dimensions

5. **Verify Accuracy**
   - Compare with known analytic solutions
   - Check convergence by refining tolerance
   - `sympy_compute.py integrate "f(x)" --var x --from a --to b`

## Tool Commands

### Scipy_Quad

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.integrate import quad; import numpy as np; result, err = quad(lambda x: np.sin(x), 0, np.pi); print('Integral:', result, 'Error:', err)"
```

### Scipy_Dblquad

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.integrate import dblquad; result, err = dblquad(lambda y, x: x*y, 0, 1, 0, 1); print('Integral:', result)"
```

### Sympy_Integrate

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" integrate "sin(x)" --var x --from 0 --to "pi"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
