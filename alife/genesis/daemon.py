"""UNATTENDED MULTI-DAY CLIMB (R173) — the world that keeps developing just by being ticked.

R169-R172 made GENESIS persistent and resumable, and PROVED (on the open-ended generative substrate)
that process death is invisible to the civilization's development: a chain of resumed segments is
bit-for-bit identical to one uninterrupted run. But the *driver* was still a verification script that
hand-drove subprocesses for the proof. R173 stands up the actual UNATTENDED loop: a single idempotent
`tick()` that any external scheduler — cron, a systemd timer, the evolving-loop supervisor, a cloud
cron — calls repeatedly against ONE on-disk `state_dir`, and which, after extending the world by one
segment, REGENERATES a rolling LIVE PANEL from the WHOLE accumulated on-disk trajectory.

So "leave it running for days and it keeps developing" becomes a real thing you start once and glance
at: every tick the world climbs one more segment and the dashboard PNG on disk refreshes to the latest
history. There is NO new simulation mechanism and NO new RNG — `tick` is a thin, resumable wrapper over
`persist.run_segment` plus a pure trajectory renderer, so the continuity guarantees proved in R169-R172
carry over unchanged: the cadence of the scheduler is irrelevant, only that it keeps ticking.
"""

from __future__ import annotations

import json
import os

import numpy as np

from alife.genesis import persist
from alife.genesis.genesis import GenesisConfig

# the live-dashboard signals (a subset of persist._KEYS) and how to title each rolling panel.
_PANELS = (
    ("conn_depth", "connected tech DEPTH (open-ended)", "#d62728"),
    ("breadth", "society repertoire breadth", "#9467bd"),
    ("realized_axes", "embodied capability axes (depth-gated)", "#ff7f0e"),
    ("edible_tiers", "embodied diet ceiling (depth-gated)", "#2ca02c"),
    ("population", "population (persistent, resumable)", "#1f77b4"),
)


def render_live_panel(traj: dict, panel_path: str, title: str = "GENESIS — unattended climb",
                      boundaries: list[float] | None = None) -> int:
    """Render the rolling live dashboard from the WHOLE accumulated trajectory and write it to
    `panel_path`. A PURE function of the trajectory dict (what every tick refreshes), so it reflects
    exactly the on-disk history — no hidden state. Returns the number of trajectory samples drawn."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steps = np.asarray(traj.get("step", np.zeros(0)))
    n = int(steps.size)
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle(f"{title}  —  {n} samples, step "
                 f"{steps[0]:.0f}->{steps[-1]:.0f}" if n else title, fontsize=13)
    for a, (key, sub, col) in zip(ax.flat[:5], _PANELS):
        y = np.asarray(traj.get(key, np.zeros(0)))
        a.plot(steps, y, color=col, lw=2, marker="o", ms=3)
        for b in (boundaries or []):
            a.axvline(b, color="0.85", lw=0.7, ls=":")
        a.set_title(sub, fontsize=10)
        a.set_xlabel("global step (across all ticks)")
    # last cell: a glanceable text read-out of the latest state (the "is it still climbing?" summary).
    a = ax[1, 2]
    a.axis("off")
    if n:
        def last(k):
            v = np.asarray(traj.get(k, np.zeros(0)))
            return v[-1] if v.size else float("nan")
        lines = [
            "LIVE STATE (latest tick)",
            f"  global step        {steps[-1]:.0f}",
            f"  population         {last('population'):.0f}",
            f"  connected depth    {last('conn_depth'):.0f}",
            f"  repertoire breadth {last('breadth'):.0f}",
            f"  diet ceiling       {last('edible_tiers'):.2f}",
            f"  capability axes    {last('realized_axes'):.2f}",
            f"  lineage diversity  {last('diversity'):.1f}",
            f"  max generation     {last('max_gen'):.0f}",
            "",
            f"  depth climbed {np.asarray(traj['conn_depth'])[0]:.0f}"
            f"->{last('conn_depth'):.0f} since start",
        ]
        a.text(0.02, 0.98, "\n".join(lines), transform=a.transAxes, va="top", ha="left",
               family="monospace", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(panel_path, dpi=110)
    plt.close(fig)
    return n


# ----------------------------------------------------------------------------------------------------
# R174: the SUSTAINED multi-day climb. R173 stood up the unattended tick loop, but with a small tree cap
# the climb SATURATED inside tick 1 — so "leave it running for days and it keeps developing" was hollow
# past the first tick. The fix is not a new mechanism but a regime: a large memory cap + a gentler
# innovation rate so the open-ended tree has headroom to keep climbing tick after tick, AND deeper
# diet/capability gates so the EMBODIED ceiling (what the BODY can eat / do) keeps rising with the depth
# rather than maxing out immediately. `climb_curve` drives that as REAL resumed ticks and records the
# per-tick frontier; the decisive falsifiable claim is the open-ended-vs-capped CONTROL — same machinery,
# only the cap differs: the uncapped world keeps climbing across the whole horizon while the capped world
# freezes once its tree is full. `render_climb_panel` draws both so the sustained climb is eye-checkable.

_CLIMB_KEYS = ("tick", "step", "conn_depth", "breadth", "edible_tiers", "realized_axes",
               "embodied_scale", "body_driver_depth", "personal_depth", "population")


def climb_curve(state_dir: str, cfg: GenesisConfig, seed: int, segment_steps: int, n_ticks: int,
                log_every: int = 20) -> dict:
    """Drive `n_ticks` REAL persistent ticks against `state_dir` and record the world's frontier at the
    end of each tick. Each tick is a `persist.run_segment` that resumes the latest on-disk checkpoint, so
    this is the genuine multi-tick climb a scheduler produces — not one in-memory run sliced for display.
    Returns per-tick arrays keyed by `_CLIMB_KEYS` (length `n_ticks`). Memory stays bounded by the world's
    fixed pools; only the last sample of each segment is kept."""
    os.makedirs(state_dir, exist_ok=True)
    rows = []
    for i in range(n_ticks):
        r = persist.run_segment(state_dir, cfg, seed=seed, segment_steps=segment_steps, log_every=log_every)
        tr = r["trajectory"]
        rows.append({
            "tick": float(i + 1), "step": float(tr["step"][-1]),
            "conn_depth": float(tr["conn_depth"][-1]), "breadth": float(tr["breadth"][-1]),
            "edible_tiers": float(tr["edible_tiers"][-1]), "realized_axes": float(tr["realized_axes"][-1]),
            "embodied_scale": float(tr["embodied_scale"][-1]),
            "body_driver_depth": float(tr["body_driver_depth"][-1]),
            "personal_depth": float(tr["personal_depth"][-1]),
            "population": float(tr["population"][-1]),
        })
    return {k: np.asarray([row[k] for row in rows]) for k in _CLIMB_KEYS}


# the four climb signals shown side by side (the repertoire frontier AND its embodied consequence).
_CLIMB_PANELS = (
    ("conn_depth", "connected tech DEPTH"),
    ("breadth", "society repertoire BREADTH"),
    ("edible_tiers", "embodied DIET ceiling (body)"),
    ("realized_axes", "embodied capability AXES (body)"),
)


def render_climb_panel(open_curve: dict, capped_curve: dict, panel_path: str,
                       title: str = "GENESIS — sustained multi-tick climb: open-ended vs capped") -> int:
    """Render the decisive open-ended-vs-capped CONTROL as a 2x2 of per-tick climb curves. The uncapped
    (open-ended) world's depth/breadth/diet/axes keep rising across ticks; the capped world freezes once
    its tree is full. A PURE function of the two climb-curve dicts. Returns the number of ticks drawn."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ot = np.asarray(open_curve.get("tick", np.zeros(0)))
    ct = np.asarray(capped_curve.get("tick", np.zeros(0)))
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle(title, fontsize=13)
    for a, (key, sub) in zip(ax.flat, _CLIMB_PANELS):
        a.plot(ot, np.asarray(open_curve.get(key, np.zeros(0))), color="#1f77b4", lw=2.2,
               marker="o", ms=4, label="open-ended (large cap)")
        a.plot(ct, np.asarray(capped_curve.get(key, np.zeros(0))), color="#d62728", lw=2.2,
               marker="s", ms=4, ls="--", label="capped (small cap) — freezes")
        a.set_title(sub, fontsize=10)
        a.set_xlabel("unattended tick")
        a.grid(alpha=0.25)
        a.legend(fontsize=8, loc="best")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(panel_path, dpi=110)
    plt.close(fig)
    return int(ot.size)


def _daemon_meta_path(state_dir: str) -> str:
    return os.path.join(state_dir, "daemon.json")


def _load_tick_count(state_dir: str) -> int:
    p = _daemon_meta_path(state_dir)
    if not os.path.exists(p):
        return 0
    with open(p) as fh:
        return int(json.load(fh).get("n_ticks", 0))


def tick(state_dir: str, cfg: GenesisConfig, seed: int, segment_steps: int,
         log_every: int = 20, panel_name: str = "live_panel.png") -> dict:
    """Run ONE unattended tick: extend the persistent world by one segment, then regenerate the rolling
    live dashboard from the whole accumulated on-disk trajectory. Idempotent across process death — a
    fresh process calling this resumes the SAME world from disk. This is the primitive an external
    scheduler (cron/systemd/supervisor/cloud cron) invokes each tick to keep the civilization developing
    while no one is watching. Returns a glanceable summary (tick_index, step span, panel info)."""
    os.makedirs(state_dir, exist_ok=True)
    r = persist.run_segment(state_dir, cfg, seed=seed, segment_steps=segment_steps, log_every=log_every)

    tick_index = _load_tick_count(state_dir) + 1
    panel_path = os.path.join(state_dir, panel_name)
    n_samples = render_live_panel(
        r["trajectory"], panel_path,
        title=f"GENESIS — unattended climb (tick {tick_index}, seed {seed})")

    with open(_daemon_meta_path(state_dir), "w") as fh:
        json.dump({"n_ticks": tick_index, "seed": seed, "segment_steps": segment_steps,
                   "log_every": log_every, "end_step": r["end_step"]}, fh)

    return {"tick_index": tick_index, "bootstrap": r["bootstrap"],
            "start_step": r["start_step"], "end_step": r["end_step"],
            "panel_path": panel_path, "panel_n_samples": n_samples}
