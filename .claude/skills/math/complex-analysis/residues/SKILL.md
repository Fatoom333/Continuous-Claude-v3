---
name: residues
description: "Problem-solving strategies for residues in complex analysis"
allowed-tools: [Bash, Read]
---

# Residues

## When to Use

Use this skill when working on residues problems in complex analysis.

## Decision Tree

1. **Computing Residues**
   - Simple pole at z0:
     - Res(f, z0) = lim\_{z->z0} (z - z0)f(z)
     - `sympy_compute.py limit "(z - <z0>)*<f>" --var z --to <z0>`
   - Pole of order n:
     - Res(f, z0) = (1/(n-1)!) \* lim d^{n-1}/dz^{n-1}[(z-z0)^n f(z)]
     - `sympy_compute.py diff "(z - <z0>)**<n>*<f>" --var z --order <n_minus_1>`, then take the limit at z0 and divide by (n-1)!
   - L'Hopital shortcut for f = g/h with simple pole:
     - Res(f, z0) = g(z0)/h'(z0)

2. **Identify Pole Order**
   - Simple pole: (z - z0)f(z) has finite limit
   - Order n: (z - z0)^n f(z) has finite limit, but (z - z0)^{n-1} f(z) doesn't
   - `sympy_compute.py limit "(z - <z0>)**<n>*<f>" --var z --to <z0>`

3. **Essential Singularities**
   - Neither pole nor removable (e.g., e^{1/z} at z=0)
   - Compute residue via Laurent series
   - `sympy_compute.py series "<f>" --var z --point <z0>` returns the Laurent series; `residue` handles it directly

4. **Apply Residue Theorem**
   - oint_C f(z)dz = 2*pi*i \* (sum of residues inside C)
   - Count only poles INSIDE the contour
   - `sympy_compute.py residue "<f>" --var z` lists every pole; keep those inside C

## Tool Commands

### Sympy_Residue

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" residue "1/((z-1)*(z-2))" --var z --at 1
```

### Sympy_Limit

```bash
# Simple pole at 1 of 1/((z-1)(z-2)): residue -1
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "(z - 1)/((z - 1)*(z - 2))" --var z --to 1
```

### Sympy_Laurent

```bash
# Essential singularity: 1 + 1/z + 1/(2z^2) + ..., so Res = 1
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" series "exp(1/z)" --var z --point 0
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" residue "exp(1/z)" --var z --at 0
```

### All_Poles

```bash
# Poles 1 and 2 with residues -1 and 1. For |z| = 3/2 only z = 1 is inside:
# the integral is 2*pi*i * (-1)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" residue "1/((z-1)*(z-2))" --var z
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
