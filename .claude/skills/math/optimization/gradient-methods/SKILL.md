---
name: gradient-methods
description: "Problem-solving strategies for gradient methods in optimization"
allowed-tools: [Bash, Read]
---

# Gradient Methods

## When to Use

Use this skill when working on gradient-methods problems in optimization.

## Decision Tree

1. **Basic Gradient Descent**
   - Update: x\_{k+1} = x_k - alpha \* grad f(x_k)
   - Step size alpha: fixed, diminishing, or line search
   - Convergence: O(1/k) for convex, linear for strongly convex

2. **Step Size Selection**
   | Method | Approach |
   |--------|----------|
   | Fixed | alpha constant (requires tuning) |
   | Backtracking | Armijo condition: f(x - alpha*grad) <= f(x) - c*alpha*||grad||^2 |
   | Exact line search | minimize f(x - alpha*grad) over alpha |
   | Adaptive | Adam, RMSprop (ML applications) |

3. **Accelerated Methods**
   - Momentum: add velocity term
   - Nesterov: look-ahead gradient
   - Conjugate gradient: for quadratic functions
   - `scipy.optimize.minimize(f, x0, method='CG')` - conjugate gradient

4. **Newton's Method**
   - Update: x\_{k+1} = x_k - H^{-1} \* grad f
   - Requires Hessian (expensive but quadratic convergence)
   - Quasi-Newton (BFGS): approximate Hessian
   - `scipy.optimize.minimize(f, x0, method='BFGS')`

5. **Convergence Diagnostics**
   - Monitor ||grad f|| < tolerance
   - Check function value decrease
   - Watch for oscillation (step size too large)
   - `sympy_compute.py diff "f" --var x` for gradient

## Tool Commands

### Scipy_Bfgs

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import minimize; res = minimize(lambda x: (x[0]-1)**2 + 100*(x[1]-x[0]**2)**2, [0, 0], method='BFGS'); print('Rosenbrock min at', res.x)"
```

### Scipy_Cg

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.optimize import minimize; res = minimize(lambda x: x[0]**2 + x[1]**2, [1, 1], method='CG'); print('Min at', res.x)"
```

### Sympy_Gradient

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" diff "x**2 + y**2" --var "[x, y]"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
