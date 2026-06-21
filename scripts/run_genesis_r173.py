"""R173 — GENESIS: the UNATTENDED MULTI-DAY CLIMB. The world you start once and leave running.

R169-R172 built persistence and PROVED process death is invisible to development. R173 stands up the
actual unattended loop: a single `daemon.tick()` that an external scheduler (cron/systemd/supervisor/
cloud cron) calls repeatedly against ONE on-disk state_dir, extending the world by a segment and then
REGENERATING a rolling LIVE PANEL from the whole accumulated trajectory. "Leave it running for days and
it keeps developing" becomes a real thing you start once and glance at.

Two modes (mirrors run_genesis_r172.py):
  tick <state_dir> <seed> <seg_steps>   run ONE unattended tick as a GENUINE separate process (the cron
                                        entrypoint): resume the world from disk, climb one segment,
                                        refresh state_dir/live_panel.png.
  (no args)                             full REAL-VERIFY: drive several `tick` runs as REAL subprocesses
                                        (true process death between every tick), confirm the on-disk
                                        history is ONE continuous monotone climb across all ticks, that
                                        depth/breadth/diet CLIMB and the live panel is regenerated each
                                        tick, and render runs/r173_daemon/{panel.png,world.gif}.
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

from alife.genesis import civdev, daemon, persist
from alife.genesis.genesis import GenesisWorld

OUT = "runs/r173_daemon"


def gen_cfg():
    """The open-ended generative + depth-gated world (== R172 gen_cfg / tests._r173_cfg). Built
    identically in parent and every subprocess so a resumed tick reconstructs the SAME world."""
    return civdev.civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=1000, innov_steps=3, n_food_tiers=5, recipe_level_step=2,
        n_capabilities=2, cap_level_step=2, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def tick_mode(state_dir, seed, seg_steps):
    r = daemon.tick(state_dir, gen_cfg(), seed=seed, segment_steps=seg_steps, log_every=20)
    traj = persist.load_trajectory(state_dir)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    print(f"  [pid {os.getpid()}] tick {r['tick_index']} {tag} steps {r['start_step']}->{r['end_step']} | "
          f"conn_depth {traj['conn_depth'][-1]:.0f} breadth {traj['breadth'][-1]:.0f} "
          f"axes {traj['realized_axes'][-1]:.2f} edible {traj['edible_tiers'][-1]:.2f} "
          f"pop {traj['population'][-1]:.0f} | panel {os.path.basename(r['panel_path'])} "
          f"({r['panel_n_samples']} samples)", flush=True)


def render_world(state_dir, seed):
    """Load the final on-disk checkpoint into a fresh world (restoring the grown tree, R172) and render a
    short orbit coloured violet->gold by realized cultural depth — the developed civilization the
    unattended loop produced, watchable proof it is alive and deep, not collapsed."""
    from alife.render3d import Renderer3D
    cfg = gen_cfg()
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    w.load_checkpoint(os.path.join(state_dir, "checkpoint.npz"))
    print(f"  render: restored world tree.n={w._tree.n} diet_ceiling={w.diet_capability_ceiling()}", flush=True)
    renderer = Renderer3D(cfg.world, width=480, height=360)
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
    seed, n_ticks = 0, 6
    # an IRREGULAR cadence on purpose — a real scheduler does not fire on an exact interval.
    seg_plan = [60, 40, 70, 50, 60, 40]
    t0 = time.time()

    # 1) drive the unattended loop as REAL separate processes (genuine process death between ticks).
    print(f"=== unattended climb: {n_ticks} REAL subprocess ticks, irregular cadence {seg_plan} "
          f"(one on-disk world in {state_dir}) ===", flush=True)
    panel = os.path.join(state_dir, "live_panel.png")
    panel_sizes = []
    for s in seg_plan:
        subprocess.run([sys.executable, os.path.abspath(__file__), "tick", state_dir,
                        str(seed), str(s)], check=True)
        panel_sizes.append(os.path.getsize(panel))      # the live dashboard regenerated each tick

    # 2) the on-disk history must be ONE continuous, advancing climb across ALL ticks (no resets/dups).
    traj = persist.load_trajectory(state_dir)
    steps = traj["step"]
    total = sum(seg_plan)
    continuous = bool(steps.size and steps[0] == 0.0 and np.all(np.diff(steps) > 0) and steps[-1] == total)
    depth_climbed = bool(traj["conn_depth"][-1] > traj["conn_depth"][0])
    breadth_climbed = bool(traj["breadth"][-1] > traj["breadth"][0])
    diet_climbed = bool(traj["edible_tiers"][-1] > traj["edible_tiers"][0])
    panel_refreshed = bool(len(set(panel_sizes)) > 1 and all(s > 1000 for s in panel_sizes))
    print(f"  on-disk: {steps.size} samples, step {steps[0]:.0f}->{steps[-1]:.0f}, continuous={continuous} | "
          f"conn_depth {traj['conn_depth'][0]:.0f}->{traj['conn_depth'][-1]:.0f} (climbed={depth_climbed}) "
          f"breadth {traj['breadth'][0]:.0f}->{traj['breadth'][-1]:.0f} (climbed={breadth_climbed}) "
          f"edible {traj['edible_tiers'][0]:.2f}->{traj['edible_tiers'][-1]:.2f} (climbed={diet_climbed})",
          flush=True)
    print(f"  live panel regenerated each tick: sizes {panel_sizes} -> refreshed={panel_refreshed}", flush=True)

    # 3) render the developed world the unattended loop produced (watchable payoff).
    nfr = render_world(state_dir, seed)

    # 4) the headline figure: the rolling live dashboard (== state_dir/live_panel.png), annotated with the
    #    real tick boundaries, so the panel IS the deliverable you would glance at after days of running.
    boundaries = list(np.cumsum(seg_plan)[:-1])
    daemon.render_live_panel(
        traj, os.path.join(OUT, "panel.png"),
        title=f"R173 GENESIS — UNATTENDED MULTI-DAY CLIMB ({n_ticks} real process ticks, irregular cadence)",
        boundaries=boundaries)

    print(f"wrote {OUT}/panel.png ({nfr} gif frames) in {time.time()-t0:.1f}s | "
          f"continuous={continuous} depth_climbed={depth_climbed} breadth_climbed={breadth_climbed} "
          f"diet_climbed={diet_climbed} panel_refreshed={panel_refreshed}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tick":
        tick_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    else:
        main()
