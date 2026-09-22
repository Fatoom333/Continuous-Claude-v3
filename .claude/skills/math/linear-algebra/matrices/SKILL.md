---
name: matrices
description: "Problem-solving strategies for matrices in linear algebra"
allowed-tools: [Bash, Read]
---

# Matrices

## When to Use

Use this skill when working on matrices problems in linear algebra.

## Decision Tree

1. **Identify Matrix Type**
   - Square, symmetric, orthogonal, diagonal?
   - Check properties with `sympy_compute.py matrix_type "<matrix>"`

2. **Basic Operations**
   - Multiplication: `sympy_compute.py matmul "<matrix_a>" "<matrix_b>"`
   - Inverse: `sympy_compute.py inverse "<matrix>"`
   - Transpose: `sympy_compute.py transpose "<matrix>"`

3. **Solve Linear Systems**
   - Ax = b: `sympy_compute.py linsolve "<matrix>" "<vector>"`
   - Output gives rank(A), rank([A|b]) (Kronecker-Capelli), free variables and RREF of [A|b]

4. **Decompositions**
   - LU: `sympy_compute.py lu "<matrix>"`
   - QR: `sympy_compute.py qr "<matrix>"`
   - SVD: `sympy_compute.py svd "<matrix>"`

## Tool Commands

### Sympy_Inverse

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" inverse "[[1,2],[3,4]]"
```

### Sympy_Det

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" det "[[a,b],[c,d]]"
```

### Sympy_Linsolve

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" linsolve "[[1,2],[3,4]]" "[5,6]"
# Equation form, variables auto-detected
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" linsolve "x + y + z = 6, x - y = 0, 2*x + z = 5"
```

### Sympy_Matrix_Type

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" matrix_type "[[0,-1],[1,0]]"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
