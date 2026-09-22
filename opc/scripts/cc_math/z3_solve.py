#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "z3-solver>=4.15",
# ]
# ///
"""Z3 constraint solving script - Cognitive prosthetics for Claude.

USAGE:
    # Check satisfiability
    uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" \
        sat "x > 0, x < 10, x*x == 49" --type int

    # Prove theorem
    uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" \
        prove "x + y == y + x" --vars x y --type int

    # Optimize
    uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" \
        optimize "x + y" --constraints "x >= 0, y >= 0, x + y <= 100" \
        --direction maximize --type real

Requires: z3-solver (pip install z3-solver)
"""

import argparse
import ast
import asyncio
import copy
import json
import re
import sys
from typing import Any


def get_z3():
    """Lazy import Z3."""
    import z3

    return z3


_KEYWORDS = {
    "And", "Or", "Not", "If", "Implies", "ForAll", "Exists", "Distinct",
    "True", "False", "and", "or", "not", "if", "else",
}


def _extract_variables(constraints: list[str]) -> list[str]:
    """Extract variable names (identifiers that are not called like functions)."""
    all_vars = set()
    for c in constraints:
        identifiers = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?!\s*\()", c)
        all_vars.update(i for i in identifiers if i not in _KEYWORDS)
    return sorted(all_vars)


def create_variables(var_specs: list[str], var_type: str = "int", bool_names=()) -> dict[str, Any]:
    """Create Z3 variables from specifications.

    Args:
        var_specs: List like ["x", "y", "z"] or ["x:int", "y:real"]
        var_type: Default type if not specified

    Returns:
        Dict mapping names to Z3 variables
    """
    z3 = get_z3()

    sorts = {
        "int": z3.IntSort(),
        "real": z3.RealSort(),
        "bool": z3.BoolSort(),
        "obj": z3.DeclareSort("U"),  # abstract domain for predicate-logic countermodels
    }

    # Sort used for undeclared functions/predicates such as P(x) or op(a, b)
    variables = {"__sort__": sorts["int"] if var_type == "bool" else sorts.get(var_type, sorts["int"])}
    for spec in var_specs:
        if ":" in spec:
            name, vtype = spec.split(":", 1)
        else:
            name, vtype = spec, "bool" if spec in bool_names else var_type
        variables[name] = z3.Const(name, sorts.get(vtype, sorts["int"]))

    return variables


def _preprocess(text: str) -> str:
    text = text.replace("&&", " and ").replace("||", " or ")
    return re.sub(r"!(?!=)", " not ", text).replace("^", "**").strip()


def _bool_names(texts: list[str]) -> set[str]:
    """Names used directly as logical operands (p in And(p, q)) are propositional variables."""
    found = set()

    def walk(node, want_bool):
        if isinstance(node, ast.Name):
            if want_bool:
                found.add(node.id)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in ("ForAll", "Exists"):
                kids = [(a, True) for a in node.args[1:]]
            elif name in _BOOL_FUNCS:
                kids = [(a, True) for a in node.args]
            elif name == "If" and node.args:
                kids = [(node.args[0], True)] + [(a, want_bool) for a in node.args[1:]]
            else:
                kids = [(a, False) for a in node.args]
            for child, flag in kids:
                walk(child, flag)
        elif isinstance(node, ast.BoolOp):
            for v in node.values:
                walk(v, True)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Not, ast.Invert)):
            walk(node.operand, True)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, _LOGIC_BINOPS):
            walk(node.left, True)
            walk(node.right, True)
        else:
            for child in ast.iter_child_nodes(node):
                walk(child, False)

    for t in texts:
        try:
            walk(ast.parse(_preprocess(t), mode="eval").body, True)
        except SyntaxError:
            pass
    return found


_BOOL_FUNCS = {"And", "Or", "Not", "Implies", "Xor"}
# &, |, ^ between formulas are logical connectives (Z3 Int has no bitwise ops)
_LOGIC_BINOPS = (ast.BitAnd, ast.BitOr)


def _declare_functions(node: ast.AST, ctx: dict, variables: dict, want_bool: bool) -> None:
    """Declare unknown called names as uninterpreted functions.

    A call in a boolean position (operand of and/or/not/Implies, quantifier body,
    top level) becomes a predicate; any other call returns the variable sort.
    """
    z3 = get_z3()

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        if name in ("ForAll", "Exists"):
            kids = [(a, True) for a in node.args[1:]]
        elif name in _BOOL_FUNCS:
            kids = [(a, True) for a in node.args]
        elif name == "If" and node.args:
            kids = [(node.args[0], True)] + [(a, want_bool) for a in node.args[1:]]
        else:
            if name not in ctx:
                sort = variables["__sort__"]
                result = z3.BoolSort() if want_bool else sort
                ctx[name] = variables[name] = z3.Function(name, *([sort] * len(node.args)), result)
            kids = [(a, False) for a in node.args]
        for child, flag in kids:
            _declare_functions(child, ctx, variables, flag)
    elif isinstance(node, ast.BoolOp):
        for v in node.values:
            _declare_functions(v, ctx, variables, True)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Not, ast.Invert)):
        _declare_functions(node.operand, ctx, variables, True)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, _LOGIC_BINOPS):
        _declare_functions(node.left, ctx, variables, True)
        _declare_functions(node.right, ctx, variables, True)
    else:
        for child in ast.iter_child_nodes(node):
            _declare_functions(child, ctx, variables, False)


class _ToZ3(ast.NodeTransformer):
    """Rewrite Python and/or/not and chained comparisons into Z3 calls."""

    @staticmethod
    def _call(name: str, args: list) -> ast.Call:
        return ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=args, keywords=[])

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        return self._call("And" if isinstance(node.op, ast.And) else "Or", node.values)

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, (ast.Not, ast.Invert)):
            return self._call("Not", [node.operand])
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, _LOGIC_BINOPS):
            return self._call("And" if isinstance(node.op, ast.BitAnd) else "Or", [node.left, node.right])
        # x**2 as x*x: Z3 solves products far faster than its power operator
        n = node.right.value if isinstance(node.right, ast.Constant) else None
        if isinstance(node.op, ast.Pow) and isinstance(n, int) and 1 <= n <= 16:
            expr = node.left
            for _ in range(n - 1):
                expr = ast.BinOp(left=expr, op=ast.Mult(), right=copy.deepcopy(node.left))
            return expr
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(node.ops) == 1:
            return node
        parts, left = [], node.left
        for op, right in zip(node.ops, node.comparators):
            parts.append(ast.Compare(left=left, ops=[op], comparators=[right]))
            left = right
        return self._call("And", parts)


def parse_constraint(constraint_str: str, variables: dict[str, Any]) -> Any:
    """Parse a constraint string into a Z3 expression.

    Accepts Python syntax plus &&, ||, !, ^ (power), chained comparisons
    (0 < x < 10), ForAll/Exists, and undeclared functions/predicates (P(x), op(a, b)),
    which are declared on first use and shared through `variables`.
    """
    z3 = get_z3()

    ctx = {k: v for k, v in variables.items() if k != "__sort__"}
    ctx.update(
        {
            "And": z3.And,
            "Or": z3.Or,
            "Not": z3.Not,
            "If": z3.If,
            "Implies": z3.Implies,
            "Xor": z3.Xor,
            "ForAll": z3.ForAll,
            "Exists": z3.Exists,
            "Distinct": z3.Distinct,
        }
    )

    try:
        tree = ast.parse(_preprocess(constraint_str), mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Cannot parse constraint '{constraint_str}': {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) or (isinstance(node, ast.Name) and node.id.startswith("_")):
            raise ValueError(f"Unsupported syntax in constraint '{constraint_str}'")

    _declare_functions(tree.body, ctx, variables, want_bool=True)
    tree = ast.fix_missing_locations(_ToZ3().visit(tree))

    try:
        return eval(compile(tree, "<constraint>", "eval"), {"__builtins__": {}}, ctx)
    except Exception as e:
        raise ValueError(f"Cannot parse constraint '{constraint_str}': {e}")


def split_constraints(text: str) -> list[str]:
    """Split on commas that are not inside (), [] or {}."""
    parts, depth, current = [], 0, []
    for ch in text:
        depth += ch in "([{"
        depth -= ch in ")]}"
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    parts.append("".join(current).strip())
    return [p for p in parts if p]


def _model_to_dict(model: Any, vars_dict: dict, variables: list[str]) -> dict:
    """Values of free variables, plus interpretations of declared functions and the domain."""
    z3 = get_z3()

    out = {}
    for v in variables:
        if v in vars_dict:
            val = model[vars_dict[v]]
            if val is not None:
                out[v] = str(val)

    functions = {d.name(): str(model[d]) for d in model.decls() if d.arity() > 0}
    if functions:
        out["functions"] = functions
    sort = vars_dict["__sort__"]
    if sort.kind() == z3.Z3_UNINTERPRETED_SORT:
        out["universe"] = [str(e) for e in (model.get_universe(sort) or [])]
    return out


def check_sat(constraints: list[str], variables: list[str] = None, var_type: str = "int") -> dict:
    """Check satisfiability and find a model if SAT.

    Args:
        constraints: List of constraint strings
        variables: Variable names (auto-detected if None)
        var_type: Default variable type

    Returns:
        {
            "satisfiable": True/False,
            "model": {...} or None,
            "reason": "..." if UNSAT
        }
    """
    z3 = get_z3()

    # Auto-detect variables if not provided
    if variables is None:
        variables = _extract_variables(constraints)

    vars_dict = create_variables(variables, var_type, _bool_names(constraints))

    solver = z3.Solver()

    for c_str in constraints:
        constraint = parse_constraint(c_str, vars_dict)
        solver.add(constraint)

    result = solver.check()

    if result == z3.sat:
        return {"satisfiable": True, "model": _model_to_dict(solver.model(), vars_dict, variables)}
    elif result == z3.unsat:
        return {"satisfiable": False, "model": None, "reason": "Constraints are unsatisfiable"}
    else:
        return {"satisfiable": None, "model": None, "reason": "Unknown (timeout or resource limit)"}


def prove_theorem(
    theorem: str, assumptions: list[str] = None, variables: list[str] = None, var_type: str = "int"
) -> dict:
    """Attempt to prove a theorem.

    Strategy: Try to find a counterexample. If UNSAT, theorem is proved.

    Args:
        theorem: Statement to prove (e.g., "x + y == y + x")
        assumptions: Preconditions
        variables: Variable names
        var_type: Variable type

    Returns:
        {
            "proved": True/False,
            "counterexample": {...} if not proved,
            "method": "...",
            "vacuous": True if assumptions are inconsistent
        }
    """
    z3 = get_z3()

    all_constraints = [theorem] + (assumptions or [])
    if variables is None:
        variables = _extract_variables(all_constraints)

    vars_dict = create_variables(variables, var_type, _bool_names(all_constraints))

    # First, check if assumptions are consistent (vacuous truth detection)
    if assumptions:
        assumption_solver = z3.Solver()
        for a_str in assumptions:
            assumption_solver.add(parse_constraint(a_str, vars_dict))
        assumption_check = assumption_solver.check()
        if assumption_check == z3.unsat:
            # Assumptions are inconsistent - vacuous truth
            return {
                "proved": True,
                "counterexample": None,
                "method": "Vacuous truth - assumptions are inconsistent",
                "vacuous": True,
                "warning": "Assumptions are inconsistent, anything can be proved",
            }

    solver = z3.Solver()

    # Add assumptions
    if assumptions:
        for a_str in assumptions:
            solver.add(parse_constraint(a_str, vars_dict))

    # Add negation of theorem (looking for counterexample)
    theorem_expr = parse_constraint(theorem, vars_dict)
    solver.add(z3.Not(theorem_expr))

    result = solver.check()

    if result == z3.unsat:
        return {"proved": True, "counterexample": None, "method": "No counterexample exists"}
    elif result == z3.sat:
        counterexample = _model_to_dict(solver.model(), vars_dict, variables)
        return {"proved": False, "counterexample": counterexample, "method": "Counterexample found"}
    else:
        return {"proved": None, "counterexample": None, "method": "Could not determine (timeout)"}


def optimize(
    objective: str,
    constraints: list[str],
    variables: list[str] = None,
    var_type: str = "real",
    direction: str = "minimize",
) -> dict:
    """Optimize an objective subject to constraints.

    Args:
        objective: Expression to optimize
        constraints: List of constraints
        variables: Variable names
        var_type: Variable type (usually "real" for optimization)
        direction: "minimize" or "maximize"

    Returns:
        {
            "optimal": True/False,
            "value": ...,
            "model": {...}
        }
    """
    z3 = get_z3()

    if variables is None:
        all_exprs = [objective] + constraints
        variables = _extract_variables(all_exprs)

    vars_dict = create_variables(variables, var_type)

    opt = z3.Optimize()

    # Add constraints
    for c_str in constraints:
        opt.add(parse_constraint(c_str, vars_dict))

    # Set objective
    obj_expr = parse_constraint(objective, vars_dict)
    if direction == "minimize":
        opt.minimize(obj_expr)
    else:
        opt.maximize(obj_expr)

    result = opt.check()

    if result == z3.sat:
        model = opt.model()
        obj_value = model.eval(obj_expr)
        return {"optimal": True, "value": str(obj_value), "model": _model_to_dict(model, vars_dict, variables)}
    elif result == z3.unsat:
        return {"optimal": False, "value": None, "model": None, "reason": "No feasible solution"}
    else:
        return {"optimal": None, "value": None, "model": None, "reason": "Unknown (timeout or resource limit)"}


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Z3 constraint solving - cognitive prosthetics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # SAT command
    sat_p = subparsers.add_parser("sat", help="Check satisfiability")
    sat_p.add_argument("constraints", help="Comma-separated constraints")
    sat_p.add_argument("--vars", nargs="+", help="Variable names")
    sat_p.add_argument("--type", dest="var_type", default="int", choices=["int", "real", "bool", "obj"])

    # Prove command
    prove_p = subparsers.add_parser("prove", help="Prove theorems")
    prove_p.add_argument("theorem", help="Statement to prove")
    prove_p.add_argument("--assume", nargs="+", help="Assumptions")
    prove_p.add_argument("--vars", nargs="+", help="Variable names")
    prove_p.add_argument("--type", dest="var_type", default="int", choices=["int", "real", "bool", "obj"])

    # Optimize command
    opt_p = subparsers.add_parser("optimize", help="Optimize objective")
    opt_p.add_argument("objective", help="Expression to optimize")
    opt_p.add_argument("--constraints", required=True, help="Comma-separated constraints")
    opt_p.add_argument("--direction", default="minimize", choices=["minimize", "maximize"])
    opt_p.add_argument("--vars", nargs="+", help="Variable names")
    opt_p.add_argument("--type", dest="var_type", default="real", choices=["int", "real", "bool"])

    # Common options
    for p in [sat_p, prove_p, opt_p]:
        p.add_argument("--json", action="store_true", help="Output as JSON")
        p.add_argument("--timeout", type=int, default=10000, help="Solver timeout in ms (default 10000)")

    args_to_parse = [arg for arg in sys.argv[1:] if not arg.endswith(".py")]
    return parser.parse_args(args_to_parse)


async def main():
    args = parse_args()
    get_z3().set_param("timeout", args.timeout)

    try:
        if args.command == "sat":
            constraints = split_constraints(args.constraints)
            result = check_sat(constraints, args.vars, args.var_type)
        elif args.command == "prove":
            result = prove_theorem(args.theorem, args.assume, args.vars, args.var_type)
        elif args.command == "optimize":
            constraints = split_constraints(args.constraints)
            result = optimize(args.objective, constraints, args.vars, args.var_type, args.direction)
        else:
            result = {"error": f"Unknown command: {args.command}"}

        # Output
        print(json.dumps(result, indent=2))

    except Exception as e:
        error_result = {"error": str(e), "command": args.command}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    asyncio.run(main())
