"""R68 — Physarum transport networks: a slime mold solves mazes and builds efficient networks.

R55 ran agent-based Physarum (a million stigmergic particles). This round is the OTHER famous
Physarum model — Tero & Nakagaki's tube-adaptation equations, the one that solved a maze and
reproduced the Tokyo rail network. The plasmodium is a network of tubes; protoplasm flows from
food source to sink through them (Poiseuille / Kirchhoff flow), and each tube ADAPTS: it
thickens where flux is high and withers where it is low. From a dense mesh of tubes this simple
positive feedback prunes the body down to the efficient routes — with one source/sink it finds
the SHORTEST PATH through a maze; with many food sources it grows an efficient transport network
whose redundancy is tuned by a single exponent. No search, no planner — just flow and adaptation.

Graph of nodes + edges; each edge has length L and conductivity D. Flux Q_ij = (D_ij/L_ij)(p_i-p_j),
pressures p solve the Kirchhoff linear system; conductivity follows dD/dt = f(|Q|) - D. numpy/CPU.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Graph:
    n: int                                  # node count
    edges: np.ndarray                       # (E,2) int node pairs
    length: np.ndarray                      # (E,) edge lengths
    pos: np.ndarray = field(default=None)   # (n,2) node coords (for drawing)


def grid_graph(w: int, h: int, blocked=None):
    """4-neighbour lattice graph. `blocked` is a set of (x,y) cells to omit (maze walls)."""
    blocked = blocked or set()
    idx = {}
    pos = []
    for y in range(h):
        for x in range(w):
            if (x, y) in blocked:
                continue
            idx[(x, y)] = len(pos)
            pos.append((x, y))
    edges, length = [], []
    for (x, y), i in idx.items():
        for dx, dy in ((1, 0), (0, 1)):
            j = idx.get((x + dx, y + dy))
            if j is not None:
                edges.append((i, j)); length.append(1.0)
    return Graph(n=len(pos), edges=np.array(edges), length=np.array(length, float),
                 pos=np.array(pos, float)), idx


def solve_flow(g: Graph, D: np.ndarray, sources: dict):
    """Solve Kirchhoff pressures and edge fluxes for conductivities D.
    `sources`: {node: injection}; must sum to 0 (e.g. +I0 at food, -I0 at sink)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve
    w = D / g.length                                   # edge conductance
    i, j = g.edges[:, 0], g.edges[:, 1]
    rows = np.concatenate([i, j, i, j])
    cols = np.concatenate([i, j, j, i])
    data = np.concatenate([w, w, -w, -w])
    L = coo_matrix((data, (rows, cols)), shape=(g.n, g.n)).tocsr()
    b = np.zeros(g.n)
    for node, inj in sources.items():
        b[node] += inj
    ground = next(iter(sources))                       # pin one node's pressure to 0 (Laplacian is singular)
    keep = np.array([k for k in range(g.n) if k != ground])
    p = np.zeros(g.n)
    p[keep] = spsolve(L[keep][:, keep].tocsc(), b[keep])
    Q = w * (p[i] - p[j])
    return p, Q


def adapt(D: np.ndarray, Q: np.ndarray, dt: float = 0.1, gamma: float = 1.0):
    """dD/dt = f(|Q|) - D, with f(q) = q^gamma/(1+q^gamma) (saturating). gamma>1 -> minimal
    tree / shortest path; gamma<1 -> robust redundant network with loops."""
    q = np.abs(Q)
    f = q ** gamma / (1.0 + q ** gamma)
    return D + dt * (f - D)


def run(g: Graph, sources: dict, steps: int = 400, gamma: float = 1.0, I0: float = 2.0,
        dt: float = 0.1, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    D = 0.5 + 0.1 * rng.random(len(g.edges))           # start with a dense, near-uniform mesh
    snaps = {}
    cost_hist = []
    for t in range(steps):
        _, Q = solve_flow(g, D, sources)
        D = adapt(D, Q, dt, gamma)
        cost_hist.append(float((D * g.length).sum()))  # total tube material
        if record_every and (t % record_every == 0 or t == steps - 1):
            snaps[t] = D.copy()
    return {"D": D, "snaps": snaps, "cost": np.array(cost_hist)}


# ----------------------------------------------------------------------------- helpers

def bfs_shortest(g: Graph, src: int, dst: int):
    """True shortest path length (in edges) via BFS, for verifying the Physarum solution."""
    from collections import deque
    adj = [[] for _ in range(g.n)]
    for (a, b) in g.edges:
        adj[a].append(b); adj[b].append(a)
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            return dist[u]
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1; q.append(v)
    return dist.get(dst, np.inf)


def solution_edges(g: Graph, D: np.ndarray, thresh: float = 0.5):
    """Edges that survived (high conductivity) = the Physarum's chosen route(s)."""
    return D > thresh


def path_from_solution(g: Graph, D: np.ndarray, src: int, dst: int, thresh: float = 0.5):
    """Trace src->dst using only surviving edges; return its length in edges (or inf)."""
    from collections import deque
    keep = D > thresh
    adj = [[] for _ in range(g.n)]
    for e, (a, b) in enumerate(g.edges):
        if keep[e]:
            adj[a].append(b); adj[b].append(a)
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            return dist[u]
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1; q.append(v)
    return dist.get(dst, np.inf)


def make_maze(w: int, h: int, seed: int = 0):
    """Recursive-backtracker perfect maze on a (w x h) cell grid; returns the set of WALL cells
    on the (2w+1 x 2h+1) node lattice and the lattice dims."""
    rng = np.random.default_rng(seed)
    W, H = 2 * w + 1, 2 * h + 1
    wall = {(x, y) for y in range(H) for x in range(W)}     # start all walls
    visited = np.zeros((w, h), bool)

    def carve(cx, cy):
        visited[cx, cy] = True
        wall.discard((2 * cx + 1, 2 * cy + 1))
        for dx, dy in rng.permutation([(1, 0), (-1, 0), (0, 1), (0, -1)]):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[nx, ny]:
                wall.discard((2 * cx + 1 + dx, 2 * cy + 1 + dy))   # remove wall between cells
                carve(nx, ny)

    import sys
    sys.setrecursionlimit(10000)
    carve(0, 0)
    return wall, W, H


def braid_maze(w: int, h: int, seed: int = 0, extra: float = 0.12):
    """A perfect maze with a fraction of interior walls removed -> LOOPS, so multiple routes of
    different lengths exist between any two points (the iconic Nakagaki maze-choice test)."""
    wall, W, H = make_maze(w, h, seed)
    rng = np.random.default_rng(seed + 1)
    # candidate removable walls: wall cells between two open cells (degree-2 walls on the lattice)
    removable = []
    for (x, y) in list(wall):
        if 0 < x < W - 1 and 0 < y < H - 1:
            if ((x - 1, y) not in wall and (x + 1, y) not in wall
                    and (x, y - 1) in wall and (x, y + 1) in wall):
                removable.append((x, y))
            elif ((x, y - 1) not in wall and (x, y + 1) not in wall
                    and (x - 1, y) in wall and (x + 1, y) in wall):
                removable.append((x, y))
    rng.shuffle(removable)
    for cell in removable[:int(len(removable) * extra)]:
        wall.discard(cell)
    return wall, W, H
