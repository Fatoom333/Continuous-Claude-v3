---
name: proof-theory
description: "Problem-solving strategies for proof theory in mathematical logic"
allowed-tools: [Bash, Read]
---

# Proof Theory

## When to Use

Use this skill when working on proof-theory problems in mathematical logic.

## Decision Tree

1. **Proof Strategy Selection**
   - Direct proof: assume premises, derive conclusion
   - Proof by contradiction: assume negation, derive false
   - Proof by cases: split on disjunction
   - Induction: base case + inductive step

2. **Structural Induction**
   - Define well-founded ordering on structures
   - Base: prove for minimal elements
   - Step: assume for smaller, prove for current
   - Base: `z3_solve.py prove "<base_case>"`; step: `z3_solve.py prove "<step_claim>" --assume "<induction_hypothesis>"`

3. **Cut Elimination**
   - Gentzen's Hauptsatz: cuts can be eliminated
   - Subformula property: only subformulas appear
   - Useful for proof normalization

4. **Completeness/Soundness Check**
   - Soundness: if provable then valid
   - Completeness: if valid then provable
   - These are meta-theorems about the proof system, not something to compute

5. **Proof Verification**
   - Check each step follows from rules
   - Verify dependencies are satisfied
   - `math_scratchpad.py chain --steps '<steps_json>'`

## Tool Commands

### Z3_Induction_Base

```bash
# Claim: 1 + 2 + ... + n = n(n+1)/2. Base case n = 1
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "1 == 1*(1 + 1)/2" --type real
```

### Z3_Induction_Step

```bash
# If s = n(n+1)/2 then s + (n+1) = (n+1)(n+2)/2
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "s + (n + 1) == (n + 1)*(n + 2)/2" --assume "s == n*(n + 1)/2" --type real
```

### Scratchpad_Chain

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/math_scratchpad.py" chain --steps '["x**2 - 4 = 0", "(x - 2)*(x + 2) = 0", "x = 2 or x = -2"]' --format text
```

### Math_Verify

```bash
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/math_scratchpad.py" verify "x = 2 implies x**2 = 4" --format text
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
