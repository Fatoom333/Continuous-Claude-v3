---
name: convex-optimization
description: "Problem-solving strategies for convex optimization in optimization"
allowed-tools: [Bash, Read]
---

# Convex Optimization

## When to Use

Use this skill when working on convex-optimization problems in optimization.

## Decision Tree

1. **Verify Convexity**
   - Objective function: Hessian positive semidefinite?
   - Constraint set: intersection of convex sets?
   - `z3_solve.py prove "hessian_psd"`

2. **Problem Classification**
   | Type | Solver |
   |------|--------|
   | Linear Programming | `scipy.optimize.linprog` |
   | Quadratic Programming | `scipy.optimize.minimize(method='SLSQP')` |
   | General Convex | Interior point methods |
   | Semidefinite | CVXPY with SDP solver |

3. **Standard Form**
   - minimize f(x) subject to g_i(x) <= 0, h_j(x) = 0
   - Convert max to min by negating
   - Convert >= to <= by negating

4. **KKT Conditions (Necessary & Sufficient)**
   - Stationarity: grad L = 0
   - Primal feasibility: g_i(x) <= 0, h_j(x) = 0
   - Dual feasibility: lambda_i >= 0
   - Complementary slackness: lambda_i \* g_i(x) = 0
   - `z3_solve.py prove "kkt_conditions"`

5. **Solve and Verify**
   - `scipy.optimize.minimize(f, x0, constraints=cons)`
   - Check constraint satisfaction
   - Verify solution is global minimum (convex guarantees this)

## Tool Commands

### Scipy_Linprog

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import linprog; res = linprog([-1, -2], A_ub=[[1, 1], [2, 1]], b_ub=[4, 5]); print('Optimal:', -res.fun, 'at x=', res.x)"
```

### Scipy_Minimize

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import minimize; res = minimize(lambda x: (x[0]-1)**2 + (x[1]-2)**2, [0, 0]); print('Minimum at', res.x)"
```

### Z3_Kkt

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "kkt_conditions"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
