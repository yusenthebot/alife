"""Ground-truth cultural CLADISTICS (R161) — does the reconstructed cladogram recover the TRUE descent?

R160 showed the deme x technique matrix is hierarchically tree-structured vs a flat column-shuffle null.
But "tree-like" is not "the RIGHT tree": there was no ground-truth line of descent to compare against, so
the strongest possible claim — that cultural-trait cladistics RECOVERS the real genealogy — could not be
made. R161 logs the actual BIRTH genealogy of the population (a parent-pointer forest) and asks the
validation question every phylogenetic method must answer: do the reconstructed inter-deme CULTURAL
distances track the inter-deme TRUE GENEALOGICAL (patristic) distances? Measured with a Mantel correlation
against a label-permutation null (the standard significance test for two distance matrices).

Pure forest/array functions; no global state, no sim coupling. The genealogy is a parent-pointer array
`parent` (node -> parent node id, < 0 for a founder/root) built append-only so a child's id always exceeds
its parent's — which lets depths be computed in one forward pass. Founders are separate roots, so the
genealogy is a FOREST; cross-founder pairs are joined at a virtual super-root at depth -1 (patristic
distance depth[a]+depth[b]+2), giving a single proper rooted tree metric over the whole population.
"""

from __future__ import annotations

import numpy as np


def build_depths(parent: np.ndarray) -> np.ndarray:
    """Generation depth of every node (founder/root = 0). Requires parent[i] < i for non-roots (true for an
    append-only birth log), so a single forward pass suffices. Returns an int64 [N] array."""
    par = np.asarray(parent, dtype=np.int64)
    n = par.shape[0]
    depth = np.zeros(n, dtype=np.int64)
    for i in range(n):
        p = par[i]
        if p >= 0:
            if p >= i:
                raise ValueError(f"genealogy not append-ordered: node {i} has parent {p} >= {i}")
            depth[i] = depth[p] + 1
    return depth


def ancestor_set(parent: np.ndarray, node: int) -> set[int]:
    """The set of ancestors of `node` including itself, up to (but not past) its root."""
    par = np.asarray(parent, dtype=np.int64)
    out, i = set(), int(node)
    while i >= 0:
        out.add(i)
        i = int(par[i])
    return out


def _lca_depth(parent: np.ndarray, depth: np.ndarray, anc_a: set[int], b: int) -> int:
    """Depth of the lowest common ancestor of a (given as its ancestor set) and b. Returns -1 if a and b
    belong to different founder trees (their only shared ancestor is the virtual super-root, depth -1)."""
    par = np.asarray(parent, dtype=np.int64)
    i = int(b)
    while i >= 0:
        if i in anc_a:
            return int(depth[i])
        i = int(par[i])
    return -1


def patristic_distance_matrix(parent: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    """[m, m] patristic (tree) distances among `nodes`: dist(a, b) = depth[a] + depth[b] - 2 * depth[LCA(a,b)],
    with the LCA depth = -1 for a cross-founder pair (joined at the virtual super-root). Symmetric, zero
    diagonal. The genuine ground-truth tree distance: how many birth events separate two individuals."""
    par = np.asarray(parent, dtype=np.int64)
    depth = build_depths(par)
    nodes = np.asarray(nodes, dtype=np.int64)
    m = nodes.shape[0]
    anc = [ancestor_set(par, int(nd)) for nd in nodes]
    D = np.zeros((m, m), dtype=float)
    for ii in range(m):
        da = int(depth[nodes[ii]])
        for jj in range(ii + 1, m):
            ld = _lca_depth(par, depth, anc[ii], int(nodes[jj]))
            d = da + int(depth[nodes[jj]]) - 2 * ld
            D[ii, jj] = D[jj, ii] = float(d)
    return D


def mantel_corr(d1: np.ndarray, d2: np.ndarray) -> float:
    """Pearson correlation between the off-diagonal (upper-triangle) entries of two [D, D] distance matrices.
    Returns nan if either matrix is degenerate (zero variance) or has < 3 taxa."""
    a, b = np.asarray(d1, dtype=float), np.asarray(d2, dtype=float)
    n = a.shape[0]
    if n < 3 or b.shape[0] != n:
        return float("nan")
    iu = np.triu_indices(n, k=1)
    x, y = a[iu], b[iu]
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _resid(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Residual of vector y after an ordinary-least-squares linear regression on x (with intercept).
    resid = y - (a + b*x); if x has no variance, regress out only the mean."""
    if x.std() < 1e-12:
        return y - y.mean()
    b = np.cov(x, y, bias=True)[0, 1] / x.var()
    return y - (y.mean() - b * x.mean()) - b * x


def partial_mantel_corr(d1: np.ndarray, d2: np.ndarray, d_ctrl: np.ndarray) -> float:
    """Partial Mantel correlation between d1 and d2 CONTROLLING for d_ctrl: the Pearson correlation of the
    residuals of d1~d_ctrl and d2~d_ctrl over the upper-triangle entries. This isolates the d1<->d2
    association that is NOT explained by the control distance (here: cultural<->genealogical correlation
    after removing the shared spatial/isolation-by-distance structure). nan if degenerate or < 3 taxa."""
    a, b, c = (np.asarray(m, dtype=float) for m in (d1, d2, d_ctrl))
    n = a.shape[0]
    if n < 3 or b.shape[0] != n or c.shape[0] != n:
        return float("nan")
    iu = np.triu_indices(n, k=1)
    x, y, z = a[iu], b[iu], c[iu]
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    rx, ry = _resid(x, z), _resid(y, z)
    if rx.std() < 1e-12 or ry.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def partial_mantel_test(d_recon: np.ndarray, d_true: np.ndarray, d_ctrl: np.ndarray,
                        n_perm: int = 999, seed: int = 20250621) -> dict:
    """Partial Mantel test: the partial correlation between the reconstructed CULTURAL distances and the TRUE
    GENEALOGICAL distances controlling for a CONTROL distance (the spatial inter-deme distance), against a
    null built by jointly permuting the taxon order (rows+cols) of the true matrix. Answers the isolation-by-
    distance red-team: does cultural distance track genealogical distance BEYOND the spatial structure both
    share? Returns {corr, null_mean, null_std, z, p, n_perm} (same shape as mantel_test)."""
    obs = partial_mantel_corr(d_recon, d_true, d_ctrl)
    dt = np.asarray(d_true, dtype=float)
    n = dt.shape[0]
    rng = np.random.default_rng(seed)
    null = []
    if not np.isnan(obs) and n >= 3:
        for _ in range(max(1, n_perm)):
            perm = rng.permutation(n)
            cc = partial_mantel_corr(d_recon, dt[np.ix_(perm, perm)], d_ctrl)
            if not np.isnan(cc):
                null.append(cc)
    arr = np.array(null, dtype=float)
    nm = float(arr.mean()) if arr.size else float("nan")
    ns = float(arr.std()) if arr.size else float("nan")
    z = float((obs - nm) / ns) if (arr.size and ns > 1e-12) else float("nan")
    p = float((np.sum(arr >= obs) + 1) / (arr.size + 1)) if arr.size else float("nan")
    return {"corr": float(obs), "null_mean": nm, "null_std": ns, "z": z, "p": p, "n_perm": int(arr.size)}


def mantel_test(d_recon: np.ndarray, d_true: np.ndarray, n_perm: int = 999, seed: int = 20250621) -> dict:
    """Mantel test: observed correlation between the reconstructed CULTURAL distances and the TRUE
    GENEALOGICAL distances, against a null built by jointly permuting the taxon order (rows+cols) of the
    true matrix. Returns {corr, null_mean, null_std, z, p, n_perm}. p = fraction of permutations whose
    correlation matches or beats the observed (one-sided). The standard significance test for whether one
    distance matrix predicts another, with the right exchangeable unit (taxa, not pairs)."""
    obs = mantel_corr(d_recon, d_true)
    dt = np.asarray(d_true, dtype=float)
    n = dt.shape[0]
    rng = np.random.default_rng(seed)
    null = []
    if not np.isnan(obs) and n >= 3:
        for _ in range(max(1, n_perm)):
            perm = rng.permutation(n)
            c = mantel_corr(d_recon, dt[np.ix_(perm, perm)])
            if not np.isnan(c):
                null.append(c)
    arr = np.array(null, dtype=float)
    nm = float(arr.mean()) if arr.size else float("nan")
    ns = float(arr.std()) if arr.size else float("nan")
    z = float((obs - nm) / ns) if (arr.size and ns > 1e-12) else float("nan")
    p = float((np.sum(arr >= obs) + 1) / (arr.size + 1)) if arr.size else float("nan")
    return {"corr": float(obs), "null_mean": nm, "null_std": ns, "z": z, "p": p, "n_perm": int(arr.size)}
