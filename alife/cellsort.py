"""R79 — Cellular Potts model: tissue sorts itself out by differential adhesion (Steinberg).

A new level: not organisms or agents but TISSUE. In the Graner-Glazier cellular Potts model a
cell is a connected blob of lattice sites sharing an ID; cells push and flow by copying their ID
into neighbouring sites, accepted by a Metropolis rule on an energy made of (a) ADHESION — every
contact between unlike cells costs an energy that depends on the two cell TYPES — and (b) an AREA
constraint that keeps cells from vanishing or ballooning. Steinberg's differential adhesion
hypothesis then predicts, and this reproduces, the classic result: a random salt-and-pepper
mixture of two cell types SORTS ITSELF OUT — like cells coalesce, the two tissues separate, and
with the right adhesion ordering the more cohesive type is engulfed by the other — exactly as
embryonic cells re-sort after being dissociated and remixed. Morphogenesis as energy minimisation.

Pure numpy/CPU; Metropolis at boundary sites.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MEDIUM = 0


@dataclass
class CPMConfig:
    size: int = 70
    cell: int = 5            # initial cell side (area ~ cell^2)
    temp: float = 8.0        # Metropolis fluctuation temperature
    lam: float = 1.0         # area-constraint stiffness
    # adhesion J[type_a][type_b]: contact cost between types (0=medium,1=A,2=B). LOWER J = MORE
    # adhesive. like-like cheaper than unlike -> sorting; medium contact expensive -> stays compact.
    J: tuple = ((0, 16, 16), (16, 2, 11), (16, 11, 2))


def init_tissue(cfg: CPMConfig, seed: int = 0, blob: bool = True):
    """Tile a central blob with small square cells, each randomly type A or B. Returns spin grid
    (cell IDs), per-cell type, per-cell area, and target area."""
    rng = np.random.default_rng(seed)
    N, c = cfg.size, cfg.cell
    spin = np.zeros((N, N), dtype=np.int64)
    types = [0]                                       # id 0 = medium
    cid = 1
    lo, hi = (N // 5, 4 * N // 5) if blob else (0, N)
    for y in range(lo, hi, c):
        for x in range(lo, hi, c):
            if blob:
                cy, cx = (y + c / 2 - N / 2), (x + c / 2 - N / 2)
                if cy * cy + cx * cx > ((hi - lo) / 2) ** 2:
                    continue                          # carve a round tissue
            spin[y:y + c, x:x + c] = cid
            types.append(int(rng.integers(1, 3)))     # type A(1) or B(2)
            cid += 1
    types = np.array(types)
    area = np.bincount(spin.ravel(), minlength=cid).astype(float)
    return spin, types, area, float(c * c)


def _neigh(y, x, N):
    return ((y - 1) % N, x), ((y + 1) % N, x), (y, (x - 1) % N), (y, (x + 1) % N)


def heterotypic_boundary(spin, types):
    """Count lattice contacts between cells of DIFFERENT type (the thing sorting minimises)."""
    t = types[spin]
    h = 0
    for ax in (0, 1):
        a = t
        b = np.roll(t, 1, axis=ax)
        ida = spin
        idb = np.roll(spin, 1, axis=ax)
        diff_cell = ida != idb
        both_cells = (a > 0) & (b > 0)
        h += int(np.sum(diff_cell & both_cells & (a != b)))
    return h


def step(cfg, spin, types, area, A0, rng, attempts=None):
    """One Monte Carlo sweep: many copy attempts at boundary sites, Metropolis-accepted."""
    N = cfg.size
    J = np.asarray(cfg.J, float)
    attempts = attempts or N * N
    for _ in range(attempts):
        y, x = int(rng.integers(N)), int(rng.integers(N))
        s = spin[y, x]
        nb = _neigh(y, x, N)
        # pick a neighbour with a different spin (a boundary site); else skip
        cands = [(ny, nx) for ny, nx in nb if spin[ny, nx] != s]
        if not cands:
            continue
        ny, nx = cands[int(rng.integers(len(cands)))]
        sn = spin[ny, nx]                              # invader spin
        ts, tn = types[s], types[sn]
        # adhesion change: site (y,x) goes s -> sn; recompute contacts with its 4 neighbours
        dH = 0.0
        for my, mx in nb:
            sm = spin[my, mx]
            tm = types[sm]
            before = J[ts, tm] if sm != s else 0.0
            after = J[tn, tm] if sm != sn else 0.0
            dH += after - before
        # area constraint (medium id 0 unconstrained)
        if s != MEDIUM:
            dH += cfg.lam * (((area[s] - 1 - A0) ** 2 - (area[s] - A0) ** 2))
        if sn != MEDIUM:
            dH += cfg.lam * (((area[sn] + 1 - A0) ** 2 - (area[sn] - A0) ** 2))
        if dH <= 0 or rng.random() < np.exp(-dH / cfg.temp):
            spin[y, x] = sn
            if s != MEDIUM:
                area[s] -= 1
            if sn != MEDIUM:
                area[sn] += 1
    return spin


def run(cfg: CPMConfig, sweeps: int, seed: int = 0, record_every: int = 0):
    rng = np.random.default_rng(seed)
    spin, types, area, A0 = init_tissue(cfg, seed)
    snaps, hetero = {}, []
    if record_every:
        snaps[0] = spin.copy()
    hetero.append(heterotypic_boundary(spin, types))
    for t in range(1, sweeps + 1):
        step(cfg, spin, types, area, A0, rng)
        hetero.append(heterotypic_boundary(spin, types))
        if record_every and (t % record_every == 0 or t == sweeps):
            snaps[t] = spin.copy()
    return {"spin": spin, "types": types, "area": area, "snaps": snaps,
            "hetero": np.array(hetero, float)}


def type_image(spin, types):
    """Map to a type image: 0 medium, 1 type A, 2 type B (for display)."""
    return types[spin]
