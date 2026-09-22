---
name: interpolation
description: "Problem-solving strategies for interpolation in numerical methods"
allowed-tools: [Bash, Read]
---

# Interpolation

## When to Use

Use this skill when working on interpolation problems in numerical methods.

## Decision Tree

1. **Assess Data Characteristics**
   - How many data points? Spacing uniform or non-uniform?
   - Is data smooth or noisy?
   - Need derivatives at endpoints?

2. **Select Interpolation Method**
   - Few points (<10): Polynomial (Lagrange, Newton)
   - Many points, smooth data: Cubic splines
   - Noisy data: Smoothing splines or least squares
   - High dimensions: Use simplex-based (n+1 neighbors vs 2^n)

3. **Implement with SciPy**
   - `scipy.interpolate.CubicSpline(x, y)` - natural cubic spline
   - `scipy.interpolate.make_interp_spline(x, y, k=3)` - B-spline
   - `scipy.interpolate.interp1d(x, y, kind='cubic')` - 1D interpolation

4. **Validate Results**
   - Check for Runge's phenomenon at boundaries (high-degree polynomials)
   - Cross-validate: leave-one-out error estimation
   - Visual inspection of interpolated curve
   - `sympy_compute.py limit "interp_error" --at boundaries`

5. **High-Dimensional Considerations**
   - Coxeter-Freudenthal-Kuhn triangulation for O(n log n) point location
   - Barycentric subdivision for balanced performance

## Tool Commands

### Scipy_Cubic_Spline

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.interpolate import CubicSpline; import numpy as np; x = np.array([0,1,2,3]); y = np.array([0,1,4,9]); cs = CubicSpline(x, y); print(cs(1.5))"
```

### Scipy_Bspline

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.interpolate import make_interp_spline; import numpy as np; x = np.array([0,1,2,3]); y = np.array([0,1,4,9]); bspl = make_interp_spline(x, y, k=3); print(bspl(1.5))"
```

### Sympy_Lagrange

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" interpolate "[(0,0),(1,1),(2,4)]" --var x
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
