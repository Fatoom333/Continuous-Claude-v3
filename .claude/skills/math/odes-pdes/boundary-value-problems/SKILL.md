---
name: boundary-value-problems
description: "Problem-solving strategies for boundary value problems in odes pdes"
allowed-tools: [Bash, Read]
---

# Boundary Value Problems

## When to Use

Use this skill when working on boundary-value-problems problems in odes pdes.

## Decision Tree

1. **Problem Classification**
   - Two-point BVP: conditions at x=a and x=b?
   - Sturm-Liouville: eigenvalue problem?
   - Mixed conditions: Dirichlet, Neumann, Robin?

2. **Shooting Method**
   - Convert BVP to IVP
   - Guess missing initial conditions
   - Iterate to satisfy boundary conditions
   - `scipy.integrate.solve_ivp` + root finding

3. **Finite Difference Method**
   - Discretize domain: x_i = a + i\*h
   - Replace derivatives with differences: y'' ~ (y*{i+1} - 2y_i + y*{i-1})/h^2
   - Solve resulting linear system
   - `sympy_compute.py linsolve "<tridiagonal_matrix>" "<rhs_vector>"`

4. **Collocation/BVP Solver**
   - `scipy.integrate.solve_bvp(ode, bc, x, y_init)`
   - Provide initial mesh and guess
   - Check residual for accuracy

5. **Eigenvalue Problems**
   - Sturm-Liouville form: -(p(x)y')' + q(x)y = lambda*w(x)*y
   - Eigenvalues are real if p, w > 0
   - Eigenfunctions orthogonal with weight w
   - Discretize and take `sympy_compute.py eigenvalues "<discretized_operator>"`, then divide by h^2

## Tool Commands

### Scipy_Solve_Bvp

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.integrate import solve_bvp; import numpy as np; ode = lambda x, y: [y[1], -y[0]]; bc = lambda ya, yb: [ya[0], yb[0]-1]; x = np.linspace(0, np.pi, 10); y = np.zeros((2, 10)); sol = solve_bvp(ode, bc, x, y); print('Solution at pi/2:', sol.sol(np.pi/2)[0])"
```

### Sympy_Linsolve

```bash
# y'' = -1, y(0) = y(1) = 0, h = 1/4: (y[i+1] - 2y[i] + y[i-1]) = -h^2 at 3 interior points
# Exact answer x(1-x)/2 gives 3/32, 1/8, 3/32
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" linsolve "[[-2,1,0],[1,-2,1],[0,1,-2]]" "[-1/16,-1/16,-1/16]"
```

### Sympy_Sturm_Liouville

```bash
# -y'' on 3 interior points: symmetric matrix, so the eigenvalues are real
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" eigenvalues "[[2,-1,0],[-1,2,-1],[0,-1,2]]"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
