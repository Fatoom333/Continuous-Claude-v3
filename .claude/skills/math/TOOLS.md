# Math Tools Reference

Complete reference for all mathematical computation tools.

## SymPy Compute (`scripts/sympy_compute.py`)

### Equation Solving

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" solve "x**2 - 4 = 0" --var x --domain real
# Returns: {"solutions": ["-2", "2"], "verified": true}
```

### Calculus

```bash
# Differentiation
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" diff "x**3 + 2*x" --var x --order 1

# Integration
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" integrate "x**2" --var x
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" integrate "x**2" --var x --bounds "[0, 1]"

# Limits
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" limit "sin(x)/x" --var x --to 0
```

### Linear Algebra

```bash
# Determinant
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" det "[[1,2],[3,4]]"

# Eigenvalues
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" eigenvalues "[[2,0],[0,3]]"

# Eigenvectors (with multiplicities)
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" eigenvectors "[[1,2],[2,1]]"

# Matrix inverse
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" inverse "[[1,2],[3,4]]"

# Transpose
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" transpose "[[1,2,3],[4,5,6]]"

# Characteristic polynomial
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" charpoly "[[1,2],[3,4]]" --var t
```

### Simplification

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "sin(x)**2 + cos(x)**2"
# Returns: {"simplified": "1"}
```

## Z3 Solve (`scripts/z3_solve.py`)

### Satisfiability

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" sat "x > 0, x < 5, x != 3"
```

### Prove/Disprove

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "x**2 >= 0"
```

## Lean 4 (Formal Verification)

### Setup

```bash
lake new my_project math
cd my_project && lake build
```

### Compiler-in-the-Loop

Write proof → `lake build` → Compiler verifies

### Key Imports

```lean
import Mathlib.CategoryTheory.Functor.Basic
import Mathlib.CategoryTheory.NatTrans
import Mathlib.CategoryTheory.Limits.Shapes.Products
```

## Output Format

All tools return JSON:

```json
{
  "result": "...",
  "latex": "\\frac{d}{dx}...",
  "verified": true
}
```

Use `--json` flag for explicit JSON output.
