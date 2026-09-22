---
name: sigma-algebras
description: "Problem-solving strategies for sigma algebras in measure theory"
allowed-tools: [Bash, Read]
---

# Sigma Algebras

## When to Use

Use this skill when working on sigma-algebras problems in measure theory.

## Decision Tree

1. **Verify sigma-algebra axioms**
   - X in F (whole space is measurable)
   - A in F implies A^c in F (closed under complements)
   - A_n in F implies union(A_n) in F (closed under countable unions)
   - `z3_solve.py prove "sigma_algebra_axioms"`

2. **sigma-algebra generation**
   - Start with generating collection C
   - sigma(C) = smallest sigma-algebra containing C
   - Use Dynkin's pi-lambda theorem for uniqueness

3. **Measurability verification**
   - f is measurable if f^{-1}(B) in F for all Borel B
   - Sufficient: check for open sets or intervals
   - `sympy_compute.py simplify "preimage(f, interval)"`

4. **Product sigma-algebras**
   - F1 x F2 = sigma{A x B : A in F1, B in F2}
   - Projections are measurable

## Tool Commands

### Z3_Sigma_Axioms

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "X_in_F and closed_under_complement and closed_under_countable_union"
```

### Z3_Dynkin_Pi_Lambda

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "pi_system_subset_lambda implies sigma_equal"
```

### Sympy_Preimage

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "f_inv(A_union_B) == f_inv(A) | f_inv(B)"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
