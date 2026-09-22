---
name: graph-algorithms
description: "Problem-solving strategies for graph algorithms in graph number theory"
allowed-tools: [Bash, Read]
---

# Graph Algorithms

## When to Use

Use this skill when working on graph-algorithms problems in graph number theory.

## Decision Tree

1. **Traversal selection**
   - BFS: shortest paths (unweighted), level structure
   - DFS: cycle detection, topological sort, SCC

2. **Shortest path algorithms**
   | Algorithm | Use Case | Complexity |
   |-----------|----------|------------|
   | Dijkstra | Non-negative weights | O((V+E) log V) |
   | Bellman-Ford | Negative weights | O(VE) |
   | Floyd-Warshall | All pairs | O(V^3) |

3. **Minimum Spanning Tree**
   - Prim's: dense graphs, greedy from vertex
   - Kruskal's: sparse graphs, union-find
   - Correctness rests on the cut property (exchange argument), proved by hand

4. **Network Flow**
   - Max-flow = min-cut (Ford-Fulkerson)
   - Matching via flow network
   - Conservation at each vertex: `sympy_compute.py linsolve "<conservation_equations>"`

5. **Graph properties**
   - Spectral: eigenvalues of adjacency matrix
   - Connectivity: via DFS/BFS
   - Coloring: greedy or SAT reduction (`z3_solve.py sat "<color_constraints>"`)

## Tool Commands

### Sympy_Adjacency

```bash
# Triangle K3: eigenvalues 2 (degree) and -1 twice
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" eigenvalues "[[0,1,1],[1,0,1],[1,1,0]]"
```

### Sympy_Walk_Count

```bash
# Entry (i, j) of A^2 counts walks of length 2 from i to j
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" matmul "[[0,1,1],[1,0,1],[1,1,0]]" "[[0,1,1],[1,0,1],[1,1,0]]"
```

### Z3_Coloring

```bash
# Is the triangle 3-colorable? Colors 0..2, adjacent vertices differ
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/z3_solve.py" sat "0 <= a <= 2, 0 <= b <= 2, 0 <= c <= 2, a != b, b != c, a != c"
```

### Sympy_Flow

```bash
# Paths s-a-t and s-b-t carry 5 units, 2 of them through a
uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/sympy_compute.py" linsolve "f_sa = f_at, f_sb = f_bt, f_sa + f_sb = 5, f_sa = 2"
```

## Cognitive Tools Reference

See the `math-unified` skill for the full command list, or run `uv run --script "$CLAUDE_OPC_DIR/scripts/cc_math/<script>.py" --help`.
