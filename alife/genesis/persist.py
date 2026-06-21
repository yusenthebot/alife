"""PERSISTENT, RESUMABLE LONG RUN (R169) — the world you leave running.

R168 assembled the full-stack civilization and proved it DEVELOPS in one ~30s run, and that a single
checkpoint reload preserves population/max_gen at the reload instant. R169 turns GENESIS into an actual
persistent PROCESS: it runs in SEGMENTS, checkpointing each segment to disk and APPENDING the
development trajectory to a durable on-disk log, so a brand-new process can resume from the latest
checkpoint and CONTINUE the same civilization — across sessions, machines, days. The CEO can leave it
running, kill it, restart it, and it keeps climbing the SAME ladder rather than starting over. This is
the literal "just by running locally or in the cloud, freely develops toward a civilization" deliverable.

THE FALSIFIABLE HEADLINE (the load-bearing claim, far stronger than R168's one-instant reload check):
a chain of K resumed segments — each a freshly-constructed `GenesisWorld` that loads the previous
segment's checkpoint, i.e. a SIMULATED PROCESS DEATH between every segment — produces a development
trajectory that is BIT-FOR-BIT IDENTICAL to one uninterrupted run of the same total length. If resume
were lossy (some stepped state not checkpointed) or non-deterministic (any RNG not restored) the
chained trajectory would DIVERGE from the continuous one. That it does not is the proof the world is
genuinely persistable: process death is invisible to the civilization's development.

`continuous_trajectory` / `chained_trajectory` are the matched pair the continuity proof compares.
`run_segment` is the persistent driver primitive: one call = "run one more segment of the world",
loading the latest on-disk checkpoint + rolling trajectory and extending both. It reuses the R168
`civdev` signals unchanged (no new simulation mechanism, no new RNG)."""

from __future__ import annotations

import json
import os

import numpy as np

from alife.genesis import civdev, techdepth
from alife.genesis.genesis import GenesisConfig, GenesisWorld

# the civilization-development signals logged per trajectory sample (same family as civdev).
_KEYS = ("step", "population", "conn_depth", "closure", "breadth",
         "realized_axes", "edible_tiers", "diversity", "max_gen")


def _observe(world: GenesisWorld) -> dict:
    """One read-only trajectory sample at the world's CURRENT step (no step, no RNG, no state change).
    Keyed by the world's global `step_count` so samples align across resume boundaries by construction."""
    snp = world.snapshot()
    known = techdepth.society_repertoire(world)
    pa, pb, level = world._tree_pa, world._tree_pb, world._tree_level
    n_seed = world.cfg.n_seed_tech
    return {
        "step": float(world.step_count),
        "population": float(snp["population"]),
        "conn_depth": float(techdepth.connected_depth(known, pa, pb, level, n_seed)),
        "closure": float(techdepth.closure_fraction(known, pa, pb, n_seed)),
        "breadth": float(known.sum()),
        "realized_axes": float(snp.get("realized_axes", np.nan)),
        "edible_tiers": float(snp.get("mean_edible_tiers", np.nan)),
        "diversity": float(snp["diversity"]),
        "max_gen": float(snp["max_gen"]),
    }


def _stack(samples: list[dict]) -> dict:
    """Stack a list of per-step sample dicts into arrays keyed by signal."""
    return {k: np.asarray([s[k] for s in samples]) for k in _KEYS}


def continuous_trajectory(cfg: GenesisConfig, seed: int, total_steps: int,
                          log_every: int = 25) -> dict:
    """One UNINTERRUPTED run of `total_steps` steps, sampling whenever the global step is a multiple of
    `log_every`. The reference the continuity proof compares the resumed chain against."""
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    samples = []
    while w.step_count < total_steps:
        if w.step_count % log_every == 0:
            samples.append(_observe(w))
        w.step()
    return _stack(samples)


def chained_trajectory(cfg: GenesisConfig, seed: int, n_segments: int, segment_steps: int,
                       ckpt_path: str, log_every: int = 25) -> dict:
    """`n_segments` segments of `segment_steps`, where EVERY boundary destroys the world object and
    rebuilds it from a checkpoint on disk (a simulated process death). Same sampling rule and same total
    length as `continuous_trajectory`, so the two must be array-equal iff resume is lossless. `segment_
    steps` must be a multiple of `log_every` so segment boundaries fall on sample points."""
    if segment_steps % log_every:
        raise ValueError("segment_steps must be a multiple of log_every for aligned sampling")
    total = n_segments * segment_steps
    samples = []
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    while w.step_count < total:
        if w.step_count % log_every == 0:
            samples.append(_observe(w))
        if w.step_count > 0 and w.step_count % segment_steps == 0:   # boundary: die + resume
            w.save_checkpoint(ckpt_path)
            del w
            w = GenesisWorld(cfg, seed=seed, evolve=True)
            w.load_checkpoint(ckpt_path)
        w.step()
    return _stack(samples)


def continuity_max_abs_diff(a: dict, b: dict) -> float:
    """Max absolute difference across every signal between two equal-length trajectories (0.0 == identical).
    NaN-vs-NaN positions (e.g. `closure` before any non-seed technique is known) count as equal; a NaN that
    appears in only one trajectory propagates to NaN (a genuine divergence)."""
    diffs = []
    for k in _KEYS:
        if not (a[k].size and b[k].size):
            continue
        both_nan = np.isnan(a[k]) & np.isnan(b[k])
        d = np.where(both_nan, 0.0, np.abs(a[k] - b[k]))
        diffs.append(float(np.max(d)))
    return max(diffs) if diffs else float("inf")


# ----------------------------------------------------------------------------------------------------
# Persistent on-disk driver: one call extends the world by one segment, resuming from the latest state.

def _paths(state_dir: str) -> tuple[str, str, str]:
    return (os.path.join(state_dir, "checkpoint.npz"),
            os.path.join(state_dir, "trajectory.npz"),
            os.path.join(state_dir, "meta.json"))


def load_trajectory(state_dir: str) -> dict:
    """Load the accumulated on-disk development trajectory (empty arrays if none yet)."""
    _, traj_path, _ = _paths(state_dir)
    if not os.path.exists(traj_path):
        return {k: np.zeros(0) for k in _KEYS}
    d = np.load(traj_path, allow_pickle=False)
    return {k: d[k] for k in _KEYS}


def run_segment(state_dir: str, cfg: GenesisConfig, seed: int, segment_steps: int,
                log_every: int = 25) -> dict:
    """Run ONE more segment of a persistent world. Loads the latest checkpoint + rolling trajectory from
    `state_dir` (or bootstraps a fresh world if none), advances `segment_steps` steps sampling every
    `log_every`, appends the new samples to the on-disk trajectory, and rewrites the checkpoint. Returns
    {trajectory, bootstrap, start_step, end_step}. This is the primitive a supervisor / cron / fresh
    `python` invocation calls each tick to keep the civilization developing unattended."""
    os.makedirs(state_dir, exist_ok=True)
    ckpt_path, traj_path, meta_path = _paths(state_dir)
    prior = load_trajectory(state_dir)
    last_step = float(prior["step"][-1]) if prior["step"].size else -1.0

    w = GenesisWorld(cfg, seed=seed, evolve=True)
    bootstrap = not os.path.exists(ckpt_path)
    if not bootstrap:
        w.load_checkpoint(ckpt_path)
    start = w.step_count
    target = start + segment_steps

    new_samples = []
    while w.step_count < target:
        if w.step_count % log_every == 0 and w.step_count > last_step:
            new_samples.append(_observe(w))
        w.step()
    if w.step_count > last_step:                                     # always log the segment end-state
        new_samples.append(_observe(w))

    w.save_checkpoint(ckpt_path)
    merged = {k: np.concatenate([prior[k], np.asarray([s[k] for s in new_samples])]) for k in _KEYS}
    np.savez_compressed(traj_path, **merged)
    with open(meta_path, "w") as fh:
        json.dump({"seed": seed, "segment_steps": segment_steps, "log_every": log_every,
                   "end_step": int(w.step_count), "n_samples": int(merged["step"].size)}, fh)
    return {"trajectory": merged, "bootstrap": bootstrap,
            "start_step": int(start), "end_step": int(w.step_count)}
