---
name: groups
description: "Problem-solving strategies for groups in abstract algebra"
allowed-tools: [Bash, Read]
---

# Groups

## When to Use

Use this skill when working on groups problems in abstract algebra.

## Decision Tree

1. **Is G a group under operation \*?**
   - Check closure: a,b in G implies a\*b in G?
   - Check associativity: (a*b)*c = a*(b*c)?
   - Check identity: exists e such that e*a = a*e = a?
   - Check inverses: for all a exists a^(-1) such that a\*a^(-1) = e?
   - Verify each axiom with `z3_solve.py prove "<axiom>" --assume <domain_conditions>`

2. **Subgroup Test**
   - Show H is non-empty (usually by showing e in H)
   - Show that for all a, b in H: ab^(-1) in H
   - `z3_solve.py prove "<ab_inverse_in_H>" --assume <a_in_H> <b_in_H>`

3. **Homomorphism Proof**
   - Verify phi(ab) = phi(a)phi(b) for all a, b in G1
   - Note: phi(e1) = e2 and phi(a^(-1)) = phi(a)^(-1) follow automatically
   - `sympy_compute.py simplify "<phi_of_ab> - <phi_a_times_phi_b>"` (0 means homomorphism)

4. **Order and Structure**
   - Element order: smallest n where a^n = e
   - Group order: |G| = number of elements
   - Lagrange: |H| divides |G| for subgroup H

## Tool Commands

### Z3_Group_Axioms

```bash
# Associativity of addition in Z_5
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "((a + b) % 5 + c) % 5 == (a + (b + c) % 5) % 5" --assume "0 <= a < 5" "0 <= b < 5" "0 <= c < 5"
```

### Z3_Subgroup

```bash
# Even integers are a subgroup of (Z, +): a, b even implies a - b even
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" prove "(a - b) % 2 == 0" --assume "a % 2 == 0" "b % 2 == 0"
```

### Sympy_Simplify

```bash
# exp: (R, +) -> (R>0, *) is a homomorphism
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" simplify "exp(a + b) - exp(a)*exp(b)"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
