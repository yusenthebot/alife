"""Cultural PHYLOGENETICS (R160) — reconstruct a cladogram of traditions and measure its tree signal.

R156/R157 established that local cultural transmission grows spatially DIVERGENT traditions (Wright's
F_ST > 0; region<->branch alignment > null). Those are FLAT statistics: they say "demes differ", not
"the differences are organised as a branching descent tree". R160 asks the cladistics question — does
the cultural trait matrix carry a real PHYLOGENETIC SIGNAL (hierarchical, nested shared-derived
techniques = synapomorphies), so a cladogram of traditions can be RECONSTRUCTED, descent-with-
modification style? Culture evolving on the open-ended tech tree should bundle whole branches of
co-occurring techniques into nested clades; a flat (non-phylogenetic) divergence would not.

Pure array functions; no global state, no sim coupling (read-only analysis over a deme x technique
matrix). Two tree-signal measures, both distance-based and construction-light:

  treelikeness  = 1 - mean Holland delta-Q over taxon quartets. For an ADDITIVE (tree-metric) distance
                  the two LARGER of a quartet's three pairing-sums are equal -> delta 0 -> treelikeness 1;
                  for reticulate/flat distances the three sums scatter -> delta ~ 1/3 -> treelikeness ~ 2/3.
  coph_corr     = Pearson correlation between the inter-taxon distances and the cophenetic distances of
                  the UPGMA tree built from them (how well a hierarchy explains the distances).

The load-bearing NULL is a COLUMN-SHUFFLE: permute each technique's presence independently across demes.
That preserves every technique's marginal frequency AND keeps demes distinct (non-degenerate distances),
but destroys the cross-technique COVARIANCE that bundles a branch's techniques into a clade. So
real > column-shuffle isolates genuine hierarchical (phylogenetic) structure, not mere divergence —
the same logic as R156/R157's position/niche shuffles.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np


def l1_distance_matrix(freqs: np.ndarray) -> np.ndarray:
    """Mean-absolute-difference (normalised L1 / Manhattan) distance between taxa rows.

    `freqs` is a [D, K] matrix of per-technique frequencies (or 0/1 presence) for D taxa over K
    techniques. Returns a [D, D] symmetric distance matrix with a zero diagonal. L1 over the boolean
    repertoire is the natural cultural distance (count of techniques that differ, normalised by K)."""
    f = np.asarray(freqs, dtype=float)
    diff = np.abs(f[:, None, :] - f[None, :, :]).mean(axis=2)
    np.fill_diagonal(diff, 0.0)
    return diff


def delta_q(dist: np.ndarray) -> float:
    """Mean Holland (2002) delta-Q over all taxon quartets — a construction-free treelikeness statistic.

    For a quartet (i,j,k,l) the three pairing-sums are s1=d_ij+d_kl, s2=d_ik+d_jl, s3=d_il+d_jk; sorted
    m1<=m2<=m3, the quartet delta is (m3-m2)/(m3-m1). An additive (perfectly tree-metric) quartet has
    m2==m3 -> delta 0; a fully ambiguous one -> delta near 1. Quartets with m3==m1 (all sums equal,
    no information) are skipped. Returns the mean over informative quartets, in [0, 1] (0 = tree-like).
    Returns nan if there are < 4 taxa or no informative quartet."""
    d = np.asarray(dist, dtype=float)
    n = d.shape[0]
    if n < 4:
        return float("nan")
    vals, eps = [], 1e-12
    for i, j, k, l in combinations(range(n), 4):
        s = np.sort([d[i, j] + d[k, l], d[i, k] + d[j, l], d[i, l] + d[j, k]])
        denom = s[2] - s[0]
        if denom > eps:
            vals.append((s[2] - s[1]) / denom)
    if not vals:
        return float("nan")
    return float(np.mean(vals))


def treelikeness(dist: np.ndarray) -> float:
    """1 - delta_q: higher = more tree-like (1 = perfectly additive tree, ~2/3 = flat/random)."""
    dq = delta_q(dist)
    return float("nan") if np.isnan(dq) else 1.0 - dq


def upgma_cophenetic(dist: np.ndarray) -> np.ndarray:
    """Build a UPGMA (average-linkage) tree from `dist` and return its [D, D] cophenetic distance matrix
    (the inter-cluster distance at which each pair of taxa is first joined). O(D^3); D is small (demes)."""
    d = np.asarray(dist, dtype=float)
    n = d.shape[0]
    M = d.copy()
    np.fill_diagonal(M, np.inf)
    size = np.ones(n)
    members = [[i] for i in range(n)]
    active = list(range(n))
    coph = np.zeros((n, n))
    while len(active) > 1:
        best, bd = None, np.inf
        for ii in range(len(active)):
            for jj in range(ii + 1, len(active)):
                a, b = active[ii], active[jj]
                if M[a, b] < bd:
                    bd, best = M[a, b], (a, b)
        a, b = best
        for x in members[a]:
            for y in members[b]:
                coph[x, y] = coph[y, x] = bd
        na, nb = size[a], size[b]
        for c in active:
            if c in (a, b):
                continue
            M[a, c] = M[c, a] = (na * M[a, c] + nb * M[b, c]) / (na + nb)
        size[a] = na + nb
        members[a] = members[a] + members[b]
        active.remove(b)
        M[b, :] = np.inf
        M[:, b] = np.inf
    return coph


def cophenetic_corr(dist: np.ndarray) -> float:
    """Pearson correlation between the observed inter-taxon distances and the cophenetic distances of the
    UPGMA tree fitted to them. High = the distances are well explained by a single nested hierarchy (a
    tree). Returns nan for < 3 taxa or a degenerate (zero-variance) distance matrix."""
    d = np.asarray(dist, dtype=float)
    n = d.shape[0]
    if n < 3:
        return float("nan")
    coph = upgma_cophenetic(d)
    iu = np.triu_indices(n, k=1)
    a, b = d[iu], coph[iu]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def informative_columns(freqs: np.ndarray) -> np.ndarray:
    """Boolean mask of techniques that VARY across taxa (peak-to-peak > 0) — the only columns that carry
    phylogenetic information. All-absent / all-present techniques contribute zero distance and zero
    signal, and would only dilute a shuffle. Returns a [K] bool mask."""
    f = np.asarray(freqs, dtype=float)
    return np.ptp(f, axis=0) > 1e-12


def column_shuffle_null(freqs: np.ndarray, n_shuffle: int, seed: int = 20250620) -> dict:
    """The load-bearing null: permute each (informative) technique column independently across taxa, so
    every technique keeps its marginal frequency and demes stay distinct, but the cross-technique
    covariance that bundles a branch into a clade is destroyed. Returns the MEAN treelikeness and
    cophenetic correlation over `n_shuffle` such permutations. Side-effect-free (its own RNG)."""
    f = np.asarray(freqs, dtype=float)[:, informative_columns(freqs)]
    if f.shape[1] == 0 or f.shape[0] < 4:
        return {"treelikeness": float("nan"), "coph_corr": float("nan")}
    rng = np.random.default_rng(seed)
    tl, cc = [], []
    D = f.shape[0]
    for _ in range(max(1, n_shuffle)):
        perm = f.copy()
        for c in range(perm.shape[1]):
            perm[:, c] = perm[rng.permutation(D), c]
        dist = l1_distance_matrix(perm)
        t, c = treelikeness(dist), cophenetic_corr(dist)
        if not np.isnan(t):
            tl.append(t)
        if not np.isnan(c):
            cc.append(c)
    return {
        "treelikeness": float(np.mean(tl)) if tl else float("nan"),
        "coph_corr": float(np.mean(cc)) if cc else float("nan"),
    }


# ---------- R163: TEMPORAL phylogeny (the time-ladder of cumulative descent) ----------
# R160-R162 reconstruct a SPATIAL phylogeny — demes are taxa, the cladogram of traditions is validated
# against the birth genealogy. R163 reconstructs the TEMPORAL phylogeny: the techniques themselves are the
# taxa, ordered in TIME by when they first appear in the population. The generative tech tree (combinatorial)
# imposes a partial order (a technique cannot be discovered before BOTH its prerequisites), so a genuine
# cumulative-descent history must (1) place every product AFTER its prereqs in time (precedence) and (2) have
# its first-appearance time track the tree DEPTH (deep techniques appear late). The ADDITIVE null (uniform
# discovery, no prereq gate) scrambles both. Pure array functions; their own RNG for the permutation null.


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (Pearson on average-ranks, ties handled). nan if < 3 points or no spread."""
    from scipy.stats import rankdata
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 3:
        return float("nan")
    rx, ry = rankdata(x), rankdata(y)
    if rx.std() < 1e-12 or ry.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def temporal_ladder_signal(first_step: np.ndarray, level: np.ndarray, pa: np.ndarray, pb: np.ndarray,
                           n_seed: int, n_perm: int = 200, seed: int = 20250620) -> dict:
    """Does the population's FIRST-APPEARANCE time of each technique RECOVER the generative tech tree —
    the time-ladder of cumulative descent?

    first_step[k] : world step at which technique k first appeared in the living population (-1 = never).
    level[k]      : tree depth of technique k (0 for seeds).
    pa, pb        : the two prerequisite ids of technique k (-1 for seeds).

    Two signals, each vs a label-permutation null over the techniques that actually appeared:
      precedence_frac : fraction of appeared non-seed techniques (whose BOTH prereqs also appeared) that
                        appear at/after both prereqs (first_step[k] >= max(first_step[pa], first_step[pb])).
                        The combinatorial mechanism forces this to 1.0; the additive null breaks it (~1/3).
      level_time_corr : Spearman correlation of tree level vs first-appearance time. High positive = the
                        history reconstructs the depth ladder (deep techniques appear late).
    """
    first = np.asarray(first_step)
    lvl = np.asarray(level, dtype=float)
    appeared = first >= 0
    idx = np.where(appeared)[0]
    out = {"n_appeared": int(idx.size)}
    nan = float("nan")
    if idx.size < 4:
        return {**out, "level_time_corr": nan, "level_time_p": nan, "level_time_null": nan,
                "precedence_frac": nan, "precedence_null": nan}
    nonseed = idx[idx >= n_seed]                                  # appeared techniques that have prerequisites
    pa, pb = np.asarray(pa), np.asarray(pb)

    def precedence(times: np.ndarray) -> float:
        ok = []
        for k in nonseed:
            a, b = int(pa[k]), int(pb[k])
            if a >= 0 and b >= 0 and times[a] >= 0 and times[b] >= 0:
                ok.append(times[k] >= max(times[a], times[b]))
        return float(np.mean(ok)) if ok else nan

    precedence_frac = precedence(first)
    corr = _spearman(lvl[idx], first[idx].astype(float))
    rng = np.random.default_rng(seed)
    null_corr, null_pre = [], []
    for _ in range(max(1, n_perm)):
        fp = first.copy()
        fp[idx] = first[rng.permutation(idx)]                    # permute appearance times among appeared taxa
        nc = _spearman(lvl[idx], fp[idx].astype(float))
        if not np.isnan(nc):
            null_corr.append(nc)
        np_ = precedence(fp)
        if not np.isnan(np_):
            null_pre.append(np_)
    null_corr = np.array(null_corr)
    level_time_null = float(null_corr.mean()) if null_corr.size else nan
    level_time_p = (float((np.abs(null_corr) >= abs(corr)).mean())
                    if (null_corr.size and not np.isnan(corr)) else nan)
    return {**out, "level_time_corr": corr, "level_time_p": level_time_p,
            "level_time_null": level_time_null, "precedence_frac": precedence_frac,
            "precedence_null": float(np.mean(null_pre)) if null_pre else nan}
