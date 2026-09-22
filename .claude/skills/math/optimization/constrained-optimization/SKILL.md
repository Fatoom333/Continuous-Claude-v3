---
name: constrained-optimization
description: "Problem-solving strategies for constrained optimization in optimization"
allowed-tools: [Bash, Read]
---

# Constrained Optimization

## When to Use

Use this skill when working on constrained-optimization problems in optimization.

## Decision Tree

1. **Constraint Classification**
   - Equality: h(x) = 0
   - Inequality: g(x) <= 0
   - Bounds: l <= x <= u

2. **Lagrangian Method (Equality Constraints)**
   - L(x, lambda) = f(x) + sum lambda_j \* h_j(x)
   - Solve: grad_x L = 0 and h(x) = 0
   - `sympy_compute.py solve "grad_L_system"`

3. **KKT Conditions (Inequality Constraints)**
   - Extend Lagrangian with mu_i for g_i(x) <= 0
   - Complementary slackness: mu_i \* g_i(x) = 0
   - `z3_solve.py prove "kkt_satisfied"`

4. **Penalty and Barrier Methods**
   - Penalty: add P(x) = rho \* sum max(0, g_i(x))^2
   - Barrier: add B(x) = -sum log(-g_i(x)) for interior point
   - Increase penalty/decrease barrier parameter iteratively

5. **SciPy Constrained Optimization**
   - `scipy.optimize.minimize(f, x0, method='SLSQP', constraints=cons)`
   - constraints = [{'type': 'eq', 'fun': h}, {'type': 'ineq', 'fun': lambda x: -g(x)}]
   - bounds = [(l1, u1), (l2, u2), ...]

## Tool Commands

### Scipy_Slsqp

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import minimize; cons = dict(type='eq', fun=lambda x: x[0] + x[1] - 1); res = minimize(lambda x: x[0]**2 + x[1]**2, [1, 1], method='SLSQP', constraints=cons); print('Min at', res.x)"
```

### Sympy_Lagrangian

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "[2*x - lam, 2*y - lam, x + y - 1]" --vars "[x, y, lam]"
```

### Z3_Kkt_Satisfied

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "complementary_slackness"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
