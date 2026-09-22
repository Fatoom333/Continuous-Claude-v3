---
name: source-coding
description: "Problem-solving strategies for source coding in information theory"
allowed-tools: [Bash, Read]
---

# Source Coding

## When to Use

Use this skill when working on source-coding problems in information theory.

## Decision Tree

1. **Source Coding Theorem**
   - Minimum average code length >= H(X)
   - Achievable with optimal codes
   - `z3_solve.py prove "shannon_bound"`

2. **Huffman Coding**
   - Optimal prefix-free code for known distribution
   - Build tree: combine two least probable symbols
   - Average length: H(X) <= L < H(X) + 1
   - `sympy_compute.py simplify "expected_code_length"`

3. **Kraft Inequality**
   - For prefix-free code: sum 2^{-l_i} <= 1
   - Necessary and sufficient
   - `z3_solve.py prove "kraft_inequality"`

4. **Arithmetic Coding**
   - Approaches entropy for any distribution
   - Encodes entire message as interval [0,1)
   - Practical for adaptive/unknown distributions

5. **Rate-Distortion Theory**
   - Lossy compression: trade rate for distortion
   - R(D) = min\_{p(x_hat|x): E[d(X,X_hat)]<=D} I(X;X_hat)
   - Minimum rate to achieve distortion D
   - `sympy_compute.py minimize "I(X;X_hat)" --constraint "E[d] <= D"`

## Tool Commands

### Scipy_Huffman

```bash
uv run --no-project --with scipy --with numpy python -c "print('Huffman codes for a=0.5, b=0.25, c=0.125, d=0.125: a=0, b=10, c=110, d=111')"
```

### Sympy_Kraft

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "2**(-l1) + 2**(-l2) + 2**(-l3) + 2**(-l4)"
```

### Z3_Shannon_Bound

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "expected_length >= entropy"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
