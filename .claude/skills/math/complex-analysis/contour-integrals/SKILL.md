---
name: contour-integrals
description: "Problem-solving strategies for contour integrals in complex analysis"
allowed-tools: [Bash, Read]
---

# Contour Integrals

## When to Use

Use this skill when working on contour-integrals problems in complex analysis.

## Decision Tree

1. **Integral Type Selection**
   - For integral\_{-inf}^{inf} f(x)dx where f decays like 1/x^a, a > 1:
     - Use semicircular contour (upper or lower half-plane)
   - For integral involving e^{ix} or trigonometric functions:
     - Close in upper half-plane for e^{ix} (Jordan's lemma)
     - Close in lower half-plane for e^{-ix}
   - For integral_0^{2pi} f(cos theta, sin theta)d theta:
     - Substitute z = e^{i theta}, use unit circle contour
   - For integrand with branch cuts:
     - Use keyhole or dogbone contour around cuts

2. **Contour Setup**
   - Identify singularities and their locations
   - Choose contour that encloses desired singularities
   - List poles and residues at once: `sympy_compute.py residue "<f>" --var z`

3. **Jordan's Lemma**
   - For integral over semicircle of radius R:
   - If |f(z)| -> 0 as |z| -> inf, semicircular contribution vanishes

4. **Compute with Residue Theorem**
   - oint_C f(z)dz = 2*pi*i \* (sum of residues inside C)
   - `sympy_compute.py residue "<f>" --var z --at <z0>`

## Tool Commands

### Sympy_Residue

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" residue "1/(z**2 + 1)" --var z --at I
```

### Sympy_Poles

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "z**2 + 1" --var z
```

### Sympy_Integrate

```bash
# Check: 2*pi*i * Res(1/(z^2 + 1), i) = 2*pi*i * (-i/2) = pi
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" integrate "1/(x**2 + 1)" --var x --lower=-oo --upper=oo
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
