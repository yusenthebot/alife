"""R169 — GENESIS: the PERSISTENT, RESUMABLE long run. The world you leave running.

Two modes:
  segment <state_dir> <seed> <seg_steps>   run ONE more segment of a persistent world (loads the latest
                                           on-disk checkpoint + rolling trajectory, extends both by one
                                           segment, exits). This is what a cron / supervisor invokes each
                                           tick — a GENUINE separate process.
  (no args)                                the full REAL-VERIFY: drive several `segment` runs as REAL
                                           SUBPROCESSES (true process death between each), confirm the
                                           on-disk trajectory continues across every restart, run the
                                           bit-for-bit continuity proof (resumed chain == uninterrupted
                                           run), and render runs/r169_persist/{panel.png, world.gif}.

Outputs to runs/r169_persist/ (gitignored):
  panel.png  — the civilization developing across the WHOLE persistent run (rebuilt from the on-disk
               trajectory), restart boundaries marked; plus the continuity-proof overlay (the resumed
               chain and the uninterrupted run lie exactly on top of each other, max|diff|=0).
  world.gif  — the developed civilization at the final checkpoint, agents coloured violet->gold by
               realized culture depth (the watchable payoff).
"""
import os
import shutil
import subprocess
import sys
import time

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis import civdev, persist
from alife.genesis.genesis import GenesisWorld

OUT = "runs/r169_persist"


def segment_mode(state_dir, seed, seg_steps):
    cfg = civdev.civ_config()
    r = persist.run_segment(state_dir, cfg, seed=seed, segment_steps=seg_steps, log_every=25)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    t = r["trajectory"]
    print(f"  [pid {os.getpid()}] {tag} steps {r['start_step']}->{r['end_step']} | "
          f"conn_depth {t['conn_depth'][-1]:.0f} breadth {t['breadth'][-1]:.0f} "
          f"axes {t['realized_axes'][-1]:.2f} edible {t['edible_tiers'][-1]:.2f} pop {t['population'][-1]:.0f}",
          flush=True)


def render_final(state_dir, seed):
    """Load the final checkpoint into a fresh world and render a short orbit coloured by culture depth."""
    from alife.render3d import Renderer3D
    cfg = civdev.civ_config()
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    w.load_checkpoint(os.path.join(state_dir, "checkpoint.npz"))
    renderer = Renderer3D(cfg.world, width=480, height=360)
    frames = []
    for i in range(36):                              # orbit the developed world; a few steps for gentle motion
        w.step()
        act = w.pop.active()
        if act.size:
            frames.append(renderer.render(w.pop.pos[act], w.pop.vel[act], civdev.capability_color(w),
                                          cam_angle=i * 0.12, cam_elev=0.42, food=w.food))
    renderer.ctx.release()
    if frames:
        imageio.mimsave(os.path.join(OUT, "world.gif"), frames, fps=12, loop=0)
    return len(frames)


def main():
    os.makedirs(OUT, exist_ok=True)
    state_dir = os.path.join(OUT, "world")
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    seed, seg_steps, n_restarts = 0, 200, 6
    t0 = time.time()

    # 1) drive the persistent world as REAL separate processes (genuine process death between segments).
    print(f"=== persistent long run: {n_restarts} REAL subprocess restarts x {seg_steps} steps "
          f"(state on disk in {state_dir}) ===", flush=True)
    for _ in range(n_restarts):
        subprocess.run([sys.executable, os.path.abspath(__file__), "segment", state_dir,
                        str(seed), str(seg_steps)], check=True)

    # 2) the on-disk trajectory must be ONE continuous, strictly-advancing history across every restart.
    traj = persist.load_trajectory(state_dir)
    steps = traj["step"]
    continuous_on_disk = bool(steps.size and steps[0] == 0.0 and np.all(np.diff(steps) > 0)
                              and steps[-1] == n_restarts * seg_steps)
    print(f"  on-disk trajectory: {steps.size} samples, step {steps[0]:.0f}->{steps[-1]:.0f}, "
          f"strictly-advancing-across-restarts={continuous_on_disk} | "
          f"conn_depth {traj['conn_depth'][0]:.0f}->{traj['conn_depth'][-1]:.0f} "
          f"breadth {traj['breadth'][0]:.0f}->{traj['breadth'][-1]:.0f} "
          f"axes ->{traj['realized_axes'][-1]:.2f} edible ->{traj['edible_tiers'][-1]:.2f}", flush=True)

    # 3) THE FALSIFIABLE HEADLINE: resumed chain == uninterrupted run, bit for bit.
    print("=== continuity proof: resumed chain (process death every segment) vs uninterrupted run ===",
          flush=True)
    cfg = civdev.civ_config()
    proof_total, proof_seg = 600, 200
    cont = persist.continuous_trajectory(cfg, seed=1, total_steps=proof_total, log_every=25)
    chain = persist.chained_trajectory(cfg, seed=1, n_segments=proof_total // proof_seg,
                                       segment_steps=proof_seg, ckpt_path=os.path.join(OUT, "_proof.npz"),
                                       log_every=25)
    mad = persist.continuity_max_abs_diff(cont, chain)
    identical = all(np.array_equal(cont[k], chain[k], equal_nan=True) for k in persist._KEYS)
    print(f"  uninterrupted vs resumed-chain over {proof_total} steps: max|diff|={mad:.3e}, "
          f"bit_for_bit_identical={identical} | both end conn_depth {cont['conn_depth'][-1]:.0f} "
          f"breadth {cont['breadth'][-1]:.0f}", flush=True)

    # 4) render the developed world (watchable payoff).
    nfr = render_final(state_dir, seed)

    # 5) panel.
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("R169 GENESIS — persistent, resumable long run (the world you leave running)", fontsize=13)
    bounds = [i * seg_steps for i in range(1, n_restarts)]
    for a, key, title, col in (
        (ax[0, 0], "conn_depth", "connected tech depth — climbs across restarts", "#d62728"),
        (ax[0, 1], "breadth", "society repertoire breadth", "#9467bd"),
        (ax[0, 2], "realized_axes", "realized physical capability axes", "#ff7f0e"),
        (ax[1, 0], "edible_tiers", "mean edible diet tiers", "#2ca02c"),
        (ax[1, 1], "population", "population (persistent, resumable)", "#1f77b4"),
    ):
        a.plot(steps, traj[key], color=col, lw=2)
        for b in bounds:
            a.axvline(b, color="0.8", lw=0.8, ls=":")
        a.set_title(title); a.set_xlabel("global step (across 6 process restarts)")
    ax[0, 1].text(0.5, 0.05, "dotted = process restart (state reloaded from disk)",
                  transform=ax[0, 1].transAxes, ha="center", fontsize=8, color="0.4")
    # continuity proof overlay: the two curves are exactly coincident.
    ax[1, 2].plot(cont["step"], cont["breadth"], color="#1f77b4", lw=5, alpha=0.4, label="uninterrupted")
    ax[1, 2].plot(chain["step"], chain["breadth"], color="#d62728", lw=1.5, ls="--",
                  label="resumed chain (death/segment)")
    ax[1, 2].set_title(f"continuity proof — coincident, max|diff|={mad:.0e}")
    ax[1, 2].set_xlabel("step"); ax[1, 2].set_ylabel("breadth"); ax[1, 2].legend(fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=110)
    os.path.exists(os.path.join(OUT, "_proof.npz")) and os.remove(os.path.join(OUT, "_proof.npz"))
    print(f"wrote {OUT}/panel.png ({nfr} gif frames) in {time.time()-t0:.1f}s | "
          f"on_disk_continuous={continuous_on_disk} continuity_identical={identical}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "segment":
        segment_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    else:
        main()
