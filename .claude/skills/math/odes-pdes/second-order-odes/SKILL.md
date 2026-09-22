---
name: second-order-odes
description: "Problem-solving strategies for second order odes in odes pdes"
allowed-tools: [Bash, Read]
---

# Second Order Odes

## When to Use

Use this skill when working on second-order-odes problems in odes pdes.

## Decision Tree

1. **Classify the ODE**
   - Constant coefficients: ay'' + by' + cy = f(x)?
   - Variable coefficients: y'' + P(x)y' + Q(x)y = R(x)?
   - Cauchy-Euler: x^2 y'' + bxy' + cy = 0?

2. **Homogeneous with Constant Coefficients**
   - Characteristic equation: ar^2 + br + c = 0
   - Distinct real roots: y = c1*e^{r1*x} + c2*e^{r2*x}
   - Repeated root: y = (c1 + c2*x)e^{r*x}
   - Complex roots a +/- bi: y = e^{ax}(c1*cos(bx) + c2*sin(bx))
   - `sympy_compute.py solve "<a>*r**2 + <b>*r + <c>" --var r`

3. **Particular Solution (Non-homogeneous)**
   - Undetermined coefficients: guess based on f(x)
   - Variation of parameters: y_p = u1*y1 + u2*y2
   - `sympy_compute.py dsolve "y'' + y = sin(x)"`

4. **Numerical Solution**
   - Convert to first-order system: let v = y', then v' = y''
   - `solve_ivp(system, [t0, tf], [y0, v0])`

5. **Boundary Value Problems**
   - Shooting method: guess initial slope, iterate
   - `scipy.integrate.solve_bvp(ode, bc, x, y_init)`

## Tool Commands

### Scipy_Solve_Ivp_System

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.integrate import solve_ivp; sol = solve_ivp(lambda t, Y: [Y[1], -Y[0]], [0, 10], [1, 0]); print('y(10) =', sol.y[0][-1])"
```

### Sympy_Charpoly

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "r**2 + r + 1" --var r
```

### Sympy_Dsolve_2Nd

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" dsolve "y'' + y = sin(x)"
# With initial conditions
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" dsolve "y'' + 4*y = 0" --ics "y(0)=1, y'(0)=0"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
