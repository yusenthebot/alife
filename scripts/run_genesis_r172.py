"""R172 — GENESIS: PERSISTENCE on the OPEN-ENDED GENERATIVE substrate. The world you leave running,
now with the GROWN tree surviving process death.

R169 made the world persistent, but on the fixed civ_config substrate (no generative tree). R172's
leap: the open-ended generative_tree + depth_gates substrate now checkpoints the GROWN tree itself, so
a resumed run keeps its connected depth AND its embodied diet ceiling instead of collapsing deep `rep`
nodes back to a fresh seed-only tree. The climb persists across real process death.

Two modes (mirrors run_genesis_persist.py):
  segment <state_dir> <seed> <seg_steps>   run ONE more segment as a GENUINE separate process.
  (no args)                                full REAL-VERIFY: drive several `segment` runs as REAL
                                           subprocesses (true process death), confirm the on-disk
                                           depth/diet trajectory keeps climbing across every restart,
                                           run the bit-for-bit continuity proof on the generative
                                           substrate, and render runs/r172_persist/{panel.png,world.gif}.
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

OUT = "runs/r172_persist"


def gen_cfg():
    """The full-stack viable GENERATIVE world whose diet tiers + capability axes are gated on cultural
    DEPTH (matches tests._depth_gate_cfg). Built identically in parent and subprocess so a resumed
    segment reconstructs the SAME world the checkpoint was written from."""
    return civdev.civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=1000, innov_steps=3, n_food_tiers=5, recipe_level_step=2,
        n_capabilities=2, cap_level_step=2, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def segment_mode(state_dir, seed, seg_steps):
    r = persist.run_segment(state_dir, gen_cfg(), seed=seed, segment_steps=seg_steps, log_every=20)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    t = r["trajectory"]
    print(f"  [pid {os.getpid()}] {tag} steps {r['start_step']}->{r['end_step']} | "
          f"conn_depth {t['conn_depth'][-1]:.0f} breadth {t['breadth'][-1]:.0f} "
          f"axes {t['realized_axes'][-1]:.2f} edible {t['edible_tiers'][-1]:.2f} pop {t['population'][-1]:.0f}",
          flush=True)


def render_final(state_dir, seed):
    """Load the final checkpoint into a fresh world and render a short orbit coloured by culture depth —
    this fresh world RESTORES the grown tree from disk (the R172 fix), so it shows the developed, deep
    civilization rather than a collapsed seed-only one."""
    from alife.render3d import Renderer3D
    cfg = gen_cfg()
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    w.load_checkpoint(os.path.join(state_dir, "checkpoint.npz"))
    print(f"  render: restored world conn_depth via tree.n={w._tree.n} "
          f"diet_ceiling={w.diet_capability_ceiling()}", flush=True)
    renderer = Renderer3D(cfg.world, width=480, height=360)
    # colour each living agent violet->gold by its REALIZED cultural DEPTH (pop.tech, level units), normalized
    # by the deepest diet-tier threshold. The depth-gate substrate has no _cap_tech, so we read depth directly.
    locked, unlocked = np.array([0.42, 0.13, 0.62]), np.array([1.0, 0.80, 0.10])
    depth_norm = max(cfg.recipe_level_step * (cfg.n_food_tiers - 1), 1)

    def depth_color(act):
        frac = np.clip(w.pop.tech[act] / depth_norm, 0.0, 1.0)[:, None]
        return locked * (1.0 - frac) + unlocked * frac

    frames = []
    for i in range(30):
        w.step()
        act = w.pop.active()
        if act.size:
            frames.append(renderer.render(w.pop.pos[act], w.pop.vel[act], depth_color(act),
                                          cam_angle=i * 0.14, cam_elev=0.42, food=w.food))
    renderer.ctx.release()
    if frames:
        imageio.mimsave(os.path.join(OUT, "world.gif"), frames, fps=12, loop=0)
    return len(frames)


def main():
    os.makedirs(OUT, exist_ok=True)
    state_dir = os.path.join(OUT, "world")
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    seed, seg_steps, n_restarts = 0, 80, 4
    t0 = time.time()

    # 1) drive the persistent GENERATIVE world as REAL separate processes (genuine process death).
    print(f"=== persistent GENERATIVE long run: {n_restarts} REAL subprocess restarts x {seg_steps} steps "
          f"(state on disk in {state_dir}) ===", flush=True)
    for _ in range(n_restarts):
        subprocess.run([sys.executable, os.path.abspath(__file__), "segment", state_dir,
                        str(seed), str(seg_steps)], check=True)

    # 2) on-disk trajectory must be ONE continuous, advancing history; depth+diet must CLIMB across restarts.
    traj = persist.load_trajectory(state_dir)
    steps = traj["step"]
    continuous = bool(steps.size and steps[0] == 0.0 and np.all(np.diff(steps) > 0)
                      and steps[-1] == n_restarts * seg_steps)
    depth_climbed = bool(traj["conn_depth"][-1] > traj["conn_depth"][0])
    diet_climbed = bool(traj["edible_tiers"][-1] > traj["edible_tiers"][0])
    print(f"  on-disk: {steps.size} samples, step {steps[0]:.0f}->{steps[-1]:.0f}, continuous={continuous} | "
          f"conn_depth {traj['conn_depth'][0]:.0f}->{traj['conn_depth'][-1]:.0f} (climbed={depth_climbed}) "
          f"edible {traj['edible_tiers'][0]:.2f}->{traj['edible_tiers'][-1]:.2f} (climbed={diet_climbed}) "
          f"axes ->{traj['realized_axes'][-1]:.2f}", flush=True)

    # 3) FALSIFIABLE HEADLINE: on the GENERATIVE substrate, resumed chain == uninterrupted run, bit for bit.
    print("=== continuity proof (GENERATIVE substrate): resumed chain vs uninterrupted run ===", flush=True)
    cfg = gen_cfg()
    proof_total, proof_seg = 120, 40
    cont = persist.continuous_trajectory(cfg, seed=1, total_steps=proof_total, log_every=20)
    chain = persist.chained_trajectory(cfg, seed=1, n_segments=proof_total // proof_seg,
                                       segment_steps=proof_seg, ckpt_path=os.path.join(OUT, "_proof.npz"),
                                       log_every=20)
    mad = persist.continuity_max_abs_diff(cont, chain)
    identical = all(np.array_equal(cont[k], chain[k], equal_nan=True) for k in persist._KEYS)
    print(f"  uninterrupted vs resumed-chain over {proof_total} steps: max|diff|={mad:.3e}, "
          f"bit_for_bit_identical={identical} | both end conn_depth {cont['conn_depth'][-1]:.0f} "
          f"edible {cont['edible_tiers'][-1]:.2f}", flush=True)

    # 4) render the developed GENERATIVE world (watchable payoff; render restores the grown tree).
    nfr = render_final(state_dir, seed)

    # 5) panel.
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("R172 GENESIS — persistence on the OPEN-ENDED generative substrate "
                 "(the grown tree survives process death)", fontsize=13)
    bounds = [i * seg_steps for i in range(1, n_restarts)]
    for a, key, title, col in (
        (ax[0, 0], "conn_depth", "connected tech DEPTH — climbs across real restarts", "#d62728"),
        (ax[0, 1], "breadth", "society repertoire breadth", "#9467bd"),
        (ax[0, 2], "realized_axes", "embodied capability axes (depth-gated)", "#ff7f0e"),
        (ax[1, 0], "edible_tiers", "embodied diet ceiling (depth-gated)", "#2ca02c"),
        (ax[1, 1], "population", "population (persistent, resumable)", "#1f77b4"),
    ):
        a.plot(steps, traj[key], color=col, lw=2, marker="o", ms=3)
        for b in bounds:
            a.axvline(b, color="0.8", lw=0.8, ls=":")
        a.set_title(title); a.set_xlabel("global step (across 4 REAL process restarts)")
    ax[0, 1].text(0.5, 0.05, "dotted = process restart (state + GROWN TREE reloaded from disk)",
                  transform=ax[0, 1].transAxes, ha="center", fontsize=8, color="0.4")
    # continuity proof overlay: the two curves are exactly coincident on the generative substrate.
    ax[1, 2].plot(cont["step"], cont["conn_depth"], color="#1f77b4", lw=5, alpha=0.4, label="uninterrupted")
    ax[1, 2].plot(chain["step"], chain["conn_depth"], color="#d62728", lw=1.5, ls="--",
                  label="resumed chain (death/segment)")
    ax[1, 2].set_title(f"continuity proof (generative) — coincident, max|diff|={mad:.0e}")
    ax[1, 2].set_xlabel("step"); ax[1, 2].set_ylabel("connected depth"); ax[1, 2].legend(fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=110)
    os.path.exists(os.path.join(OUT, "_proof.npz")) and os.remove(os.path.join(OUT, "_proof.npz"))
    print(f"wrote {OUT}/panel.png ({nfr} gif frames) in {time.time()-t0:.1f}s | "
          f"on_disk_continuous={continuous} depth_climbed={depth_climbed} diet_climbed={diet_climbed} "
          f"continuity_identical={identical}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "segment":
        segment_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    else:
        main()
