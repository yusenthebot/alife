"""R64 — Development & diversity: L-system plants and the morphospace they fill.

Every earlier genome mapped almost directly to a phenotype (a trait vector, a brain's
weights, a body's node positions). Real organisms DEVELOP: a compact genotype is unfolded
by repeated local rules into a much larger body. Lindenmayer's L-systems are the canonical
model — a tiny rewrite rule, applied a few times from a seed, grows a branching plant. The
genotype->phenotype map is recursive (a 10-symbol rule becomes thousands of segments) and
small genetic changes cause structured morphological change.

Three things this round shows:
  1. DEVELOPMENT: one rule unfolding over iterations from a seed into a plant.
  2. DIVERSITY: different rules/angles are different "species" — ferns, bushes, weeds, trees.
  3. OPEN-ENDED morphospace: there is no single "best" plant for an isolated organism (every
     scalar objective collapses to a degenerate shape — a bare spike maximises height, a flat
     sprawl maximises width). So instead of optimising one number we ILLUMINATE the space of
     forms with MAP-Elites (R28/R29): a grid over (slenderness, branchiness) where evolution
     fills each cell with the busiest plant of that shape — a whole botanical garden of
     developmental forms discovered from random grammars.

Turtle alphabet: F draw+move, +/- turn, [ ] push/pop (branch), X a placeholder the rule
expands. Pure numpy/CPU; fast.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

TOKENS = "FX+-[]"


@dataclass(frozen=True)
class Genome:
    rule: str          # the production applied to X each rewrite step
    angle: float       # turn angle in degrees


@dataclass(frozen=True)
class LSConfig:
    depth: int = 5            # rewrite iterations
    max_len: int = 3000       # cap expanded-string length (bounds runaway grammars)
    step: float = 1.0         # turtle segment length


def expand(rule: str, depth: int, max_len: int, axiom: str = "X") -> str:
    """Apply X -> rule for `depth` iterations (F and symbols pass through), capped at max_len."""
    s = axiom
    for _ in range(depth):
        if len(s) > max_len:
            break
        s = "".join(rule if c == "X" else c for c in s)
    return s[:max_len]


def turtle(s: str, angle_deg: float, step: float = 1.0) -> np.ndarray:
    """Interpret the string into line segments (M,4) = (x0,y0,x1,y1). Robust to unbalanced
    brackets (a pop on an empty stack is ignored)."""
    x, y, a = 0.0, 0.0, 90.0          # start at origin pointing up
    rad = np.pi / 180.0
    stack = []
    segs = []
    for c in s:
        if c == "F":
            nx, ny = x + step * np.cos(a * rad), y + step * np.sin(a * rad)
            segs.append((x, y, nx, ny)); x, y = nx, ny
        elif c == "+":
            a += angle_deg
        elif c == "-":
            a -= angle_deg
        elif c == "[":
            stack.append((x, y, a))
        elif c == "]":
            if stack:
                x, y, a = stack.pop()
    return np.array(segs, dtype=float).reshape(-1, 4)


def phenotype(g: Genome, cfg: LSConfig) -> np.ndarray:
    return turtle(expand(g.rule, cfg.depth, cfg.max_len), g.angle, cfg.step)


def leaf_tips(segs: np.ndarray) -> np.ndarray:
    """Branch tips = segment endpoints that start no other segment (the leaves)."""
    if len(segs) == 0:
        return np.empty((0, 2))
    ks = np.round(segs[:, 0], 3) + 1j * np.round(segs[:, 1], 3)
    ke = np.round(segs[:, 2], 3) + 1j * np.round(segs[:, 3], 3)
    return segs[:, 2:][~np.isin(ke, ks)].reshape(-1, 2)


def total_length(segs: np.ndarray) -> float:
    if len(segs) == 0:
        return 0.0
    return float(np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]).sum())


def descriptors(segs: np.ndarray):
    """(slenderness, branchiness, tip_count) of a grown plant.

    slenderness = H/(W+H) in [0,1] (0 flat sprawl .. 1 tall spike);
    branchiness = tips / segments in [0,1] (a bare shoot ~0 .. a dense bush higher)."""
    if len(segs) < 2:
        return None
    xs = np.concatenate([segs[:, 0], segs[:, 2]])
    ys = np.concatenate([segs[:, 1], segs[:, 3]])
    w, h = np.ptp(xs), np.ptp(ys)
    if w + h < 1e-9:
        return None
    tips = len(leaf_tips(segs))
    return h / (w + h), tips / len(segs), tips


# ----------------------------------------------------------------------------- evolution

def random_genome(rng) -> Genome:
    n = int(rng.integers(4, 12))
    rule = "".join(rng.choice(list(TOKENS), n))
    if "X" not in rule:
        rule += "X"
    return Genome(rule=rule, angle=float(rng.uniform(10, 45)))


def mutate(g: Genome, rng) -> Genome:
    rule = list(g.rule)
    op = rng.random()
    if op < 0.4 and rule:
        rule[rng.integers(len(rule))] = rng.choice(list(TOKENS))
    elif op < 0.7:
        rule.insert(rng.integers(len(rule) + 1), rng.choice(list(TOKENS)))
    elif op < 0.9 and len(rule) > 4:
        del rule[rng.integers(len(rule))]
    rule = "".join(rule)
    if "X" not in rule:
        rule += "X"
    angle = float(np.clip(g.angle + rng.normal(0, 6), 5, 80))
    return Genome(rule=rule[:24], angle=angle)


def map_elites(cfg: LSConfig, grid=(12, 12), iters: int = 6000, seed: int = 0):
    """Illuminate the (slenderness, branchiness) morphospace. Each cell keeps the plant with
    the MOST leaf tips for that shape; new genomes come from mutating random elites. Returns
    the archive {(i,j): (tips, genome)} and a 2D occupancy/quality map."""
    rng = np.random.default_rng(seed)
    A, B = grid
    archive = {}
    quality = np.full(grid, np.nan)

    def consider(g: Genome):
        d = descriptors(phenotype(g, cfg))
        if d is None:
            return
        slender, branchy, tips = d
        i = min(A - 1, int(slender * A))
        j = min(B - 1, int(min(branchy, 0.5) / 0.5 * B))   # branchiness rarely exceeds ~0.5
        key = (i, j)
        if key not in archive or tips > archive[key][0]:
            archive[key] = (tips, g)
            quality[i, j] = tips

    for _ in range(400):                       # seed with random genomes
        consider(random_genome(rng))
    for _ in range(iters):                      # then mutate elites
        if archive and rng.random() < 0.85:
            parent = archive[list(archive)[rng.integers(len(archive))]][1]
            consider(mutate(parent, rng))
        else:
            consider(random_genome(rng))
    return {"archive": archive, "quality": quality, "grid": grid,
            "coverage": len(archive) / (A * B)}


# A few hand-designed "species" for the diversity gallery (classic L-system grammars).
SPECIES = {
    "bushy plant": Genome("F[+X]F[-X]+X", 22.0),
    "fern": Genome("F[+X]F[-X]FX", 25.0),
    "seaweed": Genome("F[-X][+X]FX", 18.0),
    "tree": Genome("FF[+X][-X][+FX][-FX]", 28.0),
    "reed": Genome("F[+X]X", 12.0),
    "thicket": Genome("F[++X][--X][+X][-X]FX", 20.0),
}
