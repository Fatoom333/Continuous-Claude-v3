---
name: predicate-logic
description: "Problem-solving strategies for predicate logic in mathematical logic"
allowed-tools: [Bash, Read]
---

# Predicate Logic

## When to Use

Use this skill when working on predicate-logic problems in mathematical logic.

## Decision Tree

1. **Quantifier Analysis**
   - Identify: ForAll (universal), Exists (existential)
   - Scope of quantifiers and free/bound variables
   - `z3_solve.py prove "Implies(ForAll([x], P(x)), P(a))" --type obj`

2. **Prenex Normal Form**
   - Move all quantifiers to front
   - Standardize variables to avoid capture
   - Done by hand; check it with `z3_solve.py prove "<original> == <prenex_form>" --type obj`

3. **Skolemization (for Exists)**
   - Replace existential quantifiers with Skolem functions
   - Exists x. P(x) -> P(c) or P(f(y)) depending on scope
   - Needed for resolution-based proofs

4. **Resolution Proof**
   - Convert to CNF, negate conclusion
   - Apply resolution rule until empty clause or saturation
   - Cross-check validity: `z3_solve.py prove "Implies(<premises>, <conclusion>)" --type obj`

5. **Model Theory**
   - Construct countermodel to refute invalid argument
   - Finite model for finite domain
   - `z3_solve.py sat "Exists([x], P(x) & Not(Q(x)))" --type obj` (the model lists P, Q and the domain)

## Tool Commands

### Z3_Forall

```bash
# Not valid in general: Z3 answers with a countermodel
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "ForAll([x], Implies(P(x), Q(x)))" --type obj
```

### Z3_Exists

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" sat "Exists([x], And(P(x), Not(Q(x))))" --type obj
```

### Z3_Universal_Instantiation

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "Implies(ForAll([x], P(x)), P(a))" --type obj
```

### Z3_Countermodel

```bash
# "All P are Q" does not imply "all Q are P": Z3 builds a countermodel
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "Implies(ForAll([x], Implies(P(x), Q(x))), ForAll([x], Implies(Q(x), P(x))))" --type obj
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
