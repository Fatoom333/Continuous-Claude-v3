---
name: first-order-odes
description: "Problem-solving strategies for first order odes in odes pdes"
allowed-tools: [Bash, Read]
---

# First Order Odes

## When to Use

Use this skill when working on first-order-odes problems in odes pdes.

## Decision Tree

1. **Classify the ODE**
   - Linear: y' + P(x)y = Q(x)?
   - Separable: y' = f(x)g(y)?
   - Exact: M(x,y)dx + N(x,y)dy = 0 with dM/dy = dN/dx?
   - Bernoulli: y' + P(x)y = Q(x)y^n?

2. **Select Solution Method**
   | Type | Method |
   |------|--------|
   | Separable | Separate and integrate |
   | Linear | Integrating factor e^{int P dx} |
   | Exact | Find potential function |
   | Bernoulli | Substitute v = y^{1-n} |

3. **Numerical Solution (IVP)**
   - `scipy.integrate.solve_ivp(f, [t0, tf], y0, method='RK45')`
   - For stiff systems: `method='Radau'` or `method='BDF'`
   - Adaptive step size: specify rtol/atol, not step size

4. **Verify Solution**
   - Substitute back into ODE
   - Check initial/boundary conditions
   - `sympy_compute.py dsolve "y' + y = x" --ics "{y(0): 1}"`

5. **Phase Portrait (Autonomous)**
   - Find equilibria: f(y\*) = 0
   - Analyze stability: sign of f'(y\*)
   - `sympy_compute.py solve "<f_of_y>" --var y`

## Tool Commands

### Scipy_Solve_Ivp

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.integrate import solve_ivp; sol = solve_ivp(lambda t, y: -y, [0, 5], [1]); print('y(5) =', sol.y[0][-1])"
```

### Sympy_Dsolve

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" dsolve "y' + y = x" --ics "y(0)=1"
```

### Sympy_Equilibrium

```bash
# Logistic y' = y(1 - y): equilibria 0 (unstable) and 1 (stable)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "y*(1 - y)" --var y
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
