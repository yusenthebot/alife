"""R176 — GENESIS: OPEN-ENDED EMBODIMENT. The BODY keeps deepening with the tech, not ceilinged.

R171's depth_gates made the body causal on culture, but CATEGORICALLY: diet = floor(depth/step) clipped to
n_food_tiers-1, axes = count(depth>=step*(i+1)) clipped to n_capabilities. A finite tier/axis list is a ceiling
by construction, so the EMBODIED body SATURATES the instant depth crosses the last fixed threshold (R175 caveat:
diet 7 / axes 4 frozen by ~tick 1 while connected DEPTH climbs 32->76). R176 adds `depth_phenotype`: an agent's
max speed and harvest reach scale CONTINUOUSLY and UNBOUNDEDLY with its realized cultural depth, so as depth keeps
climbing the BODY keeps deepening with it — no saturation. NOT a representation change (same tree, same depth_gates
diet ladder for food); only the locomotion/reach MAPPING becomes continuous. depth_phenotype=False is byte-identical.

THE FALSIFIABLE HEADLINE — driven as GENUINE separate-process ticks (true process death between every tick), at
the R175 SUSTAINED-DEPTH regime (depth_bias on, large cap), the CONTINUOUS embodied phenotype (embodied_scale =
living-pop MEAN realized speed multiplier) keeps RISING across the WHOLE horizon (still rising on the very last
tick) while the CATEGORICAL body (realized_axes) SATURATES at its ceiling by ~tick 1 in the SAME run. The decisive
CONTROL is the GAIN itself: gain>0 -> embodied_scale climbs tick after tick; gain=0 (same depth-climbing world) ->
embodied_scale FROZEN at 1.0 though connected DEPTH climbs identically — proving it is the continuous MAPPING that
converts depth-gain into body-gain, not a relabel of depth or a run-length artifact.

Two modes (mirrors run_genesis_r175.py):
  tick <state_dir> <seed> <seg_steps> <gain>   run ONE tick as a GENUINE separate process: resume from disk,
                                               climb one segment.
  (no args)                                    full REAL-VERIFY: drive the phenotype AND zero-gain control climbs
                                               as REAL subprocess ticks, confirm the body keeps deepening while
                                               the categorical ceiling saturates, render runs/r176_body/{body.png,
                                               world.gif}.
"""
import os
import shutil
import subprocess
import sys
import time

import imageio.v2 as imageio
import numpy as np

from alife.genesis import daemon, persist
from alife.genesis.civdev import civ_config
from alife.genesis.genesis import GenesisWorld

OUT = "runs/r176_body"


def r176_cfg(gain, K=20000):
    """The R175 SUSTAINED-DEPTH regime (depth_bias on, large cap, deep gates) + the R176 continuous body.
    The phenotype-vs-control changes the GAIN alone — same depth-climbing world underneath."""
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        depth_phenotype=True, pheno_speed_gain=gain, pheno_reach_gain=gain,
        max_techniques=K, innov_steps=2, n_food_tiers=8, recipe_level_step=2,
        n_capabilities=4, cap_level_step=3, tier0_frac=0.4, depth_bias=1.0,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def tick_mode(state_dir, seed, seg, gain):
    r = daemon.tick(state_dir, r176_cfg(gain), seed=seed, segment_steps=seg, log_every=20)
    tr = persist.load_trajectory(state_dir)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    print(f"  [pid {os.getpid()}] gain={gain} tick {r['tick_index']} {tag} steps {r['start_step']}->{r['end_step']} | "
          f"depth {tr['conn_depth'][-1]:.0f} body_scale {tr['embodied_scale'][-1]:.3f} "
          f"axes {tr['realized_axes'][-1]:.2f} pop {tr['population'][-1]:.0f}", flush=True)


def drive_real_ticks(tag, state_dir, seed, seg, n_ticks, gain):
    """Drive `n_ticks` ticks as REAL separate subprocesses (genuine process death between every tick)."""
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    print(f"--- {tag}: {n_ticks} REAL subprocess ticks, gain={gain} ({state_dir}) ---", flush=True)
    for _ in range(n_ticks):
        subprocess.run([sys.executable, os.path.abspath(__file__), "tick", state_dir,
                        str(seed), str(seg), str(gain)], check=True)
    tr = persist.load_trajectory(state_dir)
    ends = np.where(tr["step"] % seg == 0)[0][1:]      # one last-of-segment sample per tick
    keys = ("step", "conn_depth", "breadth", "edible_tiers", "realized_axes", "embodied_scale", "population")
    return {k: tr[k][ends] for k in keys}


def render_world(state_dir, seed, gain):
    """Render the developed open-ended civilization (violet->gold by cultural depth) — watchable proof the
    continuous-body climb produced a deep, alive population, not a frozen or collapsed one."""
    from alife.render3d import Renderer3D
    cfg = r176_cfg(gain)
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    w.load_checkpoint(os.path.join(state_dir, "checkpoint.npz"))
    print(f"  render: restored tree.n={w._tree.n} diet_ceiling={w.diet_capability_ceiling()} "
          f"body_scale={w.embodied_scale()['mean_speed_mult']:.3f}", flush=True)
    renderer = Renderer3D(cfg.world, width=480, height=360)
    locked, unlocked = np.array([0.42, 0.13, 0.62]), np.array([1.0, 0.80, 0.10])
    depth_norm = max(cfg.recipe_level_step * (cfg.n_food_tiers - 1), 1)
    frames = []
    for i in range(30):
        w.step()
        act = w.pop.active()
        if act.size:
            frac = np.clip(w.pop.tech[act] / depth_norm, 0.0, 1.0)[:, None]
            col = locked * (1.0 - frac) + unlocked * frac
            frames.append(renderer.render(w.pop.pos[act], w.pop.vel[act], col,
                                          cam_angle=i * 0.14, cam_elev=0.42, food=w.food))
    renderer.ctx.release()
    if frames:
        imageio.mimsave(os.path.join(OUT, "world.gif"), frames, fps=12, loop=0)
    return len(frames)


def render_body_panel(pheno, ctrl, path, title):
    """2x2 continuous-body-vs-zero-gain-control per-tick climb. The headline panel is embodied_scale (continuous
    body keeps deepening); realized_axes (categorical) saturates; conn_depth climbs in BOTH (the shared driver)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    panels = (("embodied_scale", "CONTINUOUS body: mean speed mult (the R176 target)"),
              ("realized_axes", "CATEGORICAL body: capability AXES (saturates)"),
              ("conn_depth", "connected tech DEPTH (the shared driver)"),
              ("population", "living population"))
    n = np.arange(1, pheno["embodied_scale"].size + 1)
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle(title, fontsize=13)
    for a, (key, sub) in zip(ax.flat, panels):
        a.plot(n, np.asarray(pheno[key]), color="#1f77b4", lw=2.2, marker="o", ms=4,
               label="depth_phenotype (gain=0.02) — body keeps deepening")
        a.plot(n, np.asarray(ctrl[key]), color="#d62728", lw=2.2, marker="s", ms=4, ls="--",
               label="zero-gain control (gain=0) — body frozen")
        a.set_title(sub, fontsize=10)
        a.set_xlabel("unattended tick")
        a.grid(alpha=0.25)
        a.legend(fontsize=8, loc="best")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return int(n.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    seed, n_ticks, seg = 0, 8, 50
    half = n_ticks // 2
    t0 = time.time()

    pheno = drive_real_ticks("CONTINUOUS body (depth_phenotype)", os.path.join(OUT, "pheno"), seed, seg, n_ticks, 0.02)
    ctrl = drive_real_ticks("ZERO-GAIN control", os.path.join(OUT, "ctrl"), seed, seg, n_ticks, 0.0)

    # the falsifiable verdict (same family as the unit test, on genuine separate-process histories)
    body_climbs_late = bool(pheno["embodied_scale"][-1] > pheno["embodied_scale"][half] + 0.05)
    body_still_deepening = bool(pheno["embodied_scale"][-1] - pheno["embodied_scale"][-2] > 0.0)
    axes_saturate = bool(pheno["realized_axes"][-1] == pheno["realized_axes"][half])
    ctrl_body_frozen = bool(np.allclose(ctrl["embodied_scale"], 1.0))
    depth_climbs_both = bool(pheno["conn_depth"][-1] > pheno["conn_depth"][0] + 10
                             and ctrl["conn_depth"][-1] > ctrl["conn_depth"][0] + 10)
    alive = bool(pheno["population"][-1] >= 500 and ctrl["population"][-1] >= 500)

    print(f"\n  PHENO body_scale/tick: {' '.join(f'{d:.3f}' for d in pheno['embodied_scale'])}", flush=True)
    print(f"  PHENO axes/tick:       {' '.join(f'{a:.0f}' for a in pheno['realized_axes'])}", flush=True)
    print(f"  PHENO depth/tick:      {' '.join(f'{d:.0f}' for d in pheno['conn_depth'])}", flush=True)
    print(f"  CTRL  body_scale/tick: {' '.join(f'{d:.3f}' for d in ctrl['embodied_scale'])}", flush=True)
    print(f"  CTRL  depth/tick:      {' '.join(f'{d:.0f}' for d in ctrl['conn_depth'])}", flush=True)
    print(f"  VERDICT: body_climbs_late={body_climbs_late} body_still_deepening={body_still_deepening} "
          f"axes_saturate={axes_saturate} ctrl_body_frozen={ctrl_body_frozen} "
          f"depth_climbs_both={depth_climbs_both} alive={alive}", flush=True)

    render_body_panel(pheno, ctrl, os.path.join(OUT, "body.png"),
                      title=f"R176 GENESIS — OPEN-ENDED BODY across {n_ticks} real process ticks: continuous "
                            f"depth_phenotype keeps deepening vs categorical axes saturate (same depth-climbing world)")
    nfr = render_world(os.path.join(OUT, "pheno"), seed, 0.02)

    ok = (body_climbs_late and body_still_deepening and axes_saturate and ctrl_body_frozen
          and depth_climbs_both and alive)
    print(f"\nwrote {OUT}/body.png + world.gif ({nfr} frames) in {time.time()-t0:.1f}s | PASS={ok}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tick":
        tick_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]))
    else:
        main()
