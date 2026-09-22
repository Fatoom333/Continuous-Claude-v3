---
name: channel-capacity
description: "Problem-solving strategies for channel capacity in information theory"
allowed-tools: [Bash, Read]
---

# Channel Capacity

## When to Use

Use this skill when working on channel-capacity problems in information theory.

## Decision Tree

1. **Mutual Information**
   - I(X;Y) = H(X) + H(Y) - H(X,Y)
   - I(X;Y) = H(X) - H(X|Y) = H(Y) - H(Y|X)
   - Symmetric: I(X;Y) = I(Y;X)
   - `scipy.stats.entropy(p) + scipy.stats.entropy(q) - joint_entropy`

2. **Channel Model**
   - Input X, output Y, channel P(Y|X)
   - Channel matrix: rows = inputs, columns = outputs
   - Element (i,j) = P(Y=j | X=i)

3. **Channel Capacity**
   - C = max\_{p(x)} I(X;Y)
   - Maximize over input distribution
   - Achieved by capacity-achieving distribution

4. **Common Channels**
   | Channel | Capacity |
   |---------|----------|
   | Binary Symmetric (BSC) | 1 - H(p) where p = crossover prob |
   | Binary Erasure (BEC) | 1 - epsilon where epsilon = erasure prob |
   | AWGN | 0.5 \* log2(1 + SNR) |

5. **Blahut-Arimoto Algorithm**
   - Iterative algorithm to compute capacity
   - Alternates between optimizing p(x) and p(y|x)
   - Converges to capacity
   - `z3_solve.py prove "capacity_upper_bound"`

## Tool Commands

### Scipy_Mutual_Info

```bash
uv run --no-project --with scipy --with numpy python -c "from scipy.stats import entropy; p = [0.5, 0.5]; q = [0.6, 0.4]; H_X = entropy(p, base=2); H_Y = entropy(q, base=2); print('H(X)=', H_X, 'H(Y)=', H_Y)"
```

### Sympy_Bsc_Capacity

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "1 + p*log(p, 2) + (1-p)*log(1-p, 2)"
```

### Z3_Capacity_Bound

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "I(X;Y) <= H(X)"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
