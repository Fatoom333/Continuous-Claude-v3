---
name: eigenvalues
description: "Problem-solving strategies for eigenvalues in linear algebra"
allowed-tools: [Bash, Read]
---

# Eigenvalues

## When to Use

Use this skill when working on eigenvalues problems in linear algebra.

## Decision Tree

1. **Compute Characteristic Polynomial**
   - det(A - lambda\*I) = 0
   - `sympy_compute.py charpoly "[[a,b],[c,d]]" --var lam`

2. **Find Eigenvalues**
   - Solve characteristic polynomial
   - `sympy_compute.py eigenvalues "[[1,2],[3,4]]"`

3. **Find Eigenvectors**
   - For each eigenvalue lambda: solve (A - lambda\*I)v = 0
   - `sympy_compute.py eigenvectors "[[1,2],[3,4]]"`

4. **Verify**
   - Check Av = lambda\*v: `sympy_compute.py matmul "<matrix>" "<eigenvector>"`
   - Verify algebraic/geometric multiplicity

## Tool Commands

### Sympy_Eigenvalues

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" eigenvalues "[[1,2],[3,4]]"
```

### Sympy_Charpoly

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" charpoly "[[a,b],[c,d]]" --var lam
```

### Verify_Av_equals_lambda_v

```bash
# v = (1, 1) with lambda = 3 for A = [[2,1],[1,2]]: expect [[3], [3]]
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" matmul "[[2,1],[1,2]]" "[[1],[1]]"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
