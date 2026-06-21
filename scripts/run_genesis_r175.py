"""R175 — GENESIS: SUSTAINED connected DEPTH, not just breadth. Push the open-ended ceiling past R174's caveat.

R174 proved the unattended world keeps DEVELOPING across many real ticks, but with an honest caveat: under
the UNIFORM composition draw, society BREADTH climbs the whole horizon while connected tech DEPTH PLATEAUS by
~tick 6. The cause is structural — max connected depth advances only when the current-deepest technique is one
of the two re-composed, and a uniform draw picks it just ~2/|known| of the time, a probability that VANISHES as
breadth grows, so depth growth decelerates and stalls.

R175 adds the missing cultural-evolution force: `depth_bias` makes the per-composition draw a SOFTMAX over tree
LEVEL (exp(depth_bias*level)), so the DEEPEST techniques are preferentially re-composed — preferential reuse,
"the rich get richer" on the frontier. NOT a representation change (same tree, same compose rule); only the
SELECTION of which two techniques to combine differs. depth_bias=0.0 is byte-identical to the R170-R174 path.

THE FALSIFIABLE HEADLINE — the depth-biased-vs-unbiased CONTROL, driven as GENUINE separate-process ticks
(true process death between every tick), at a LARGE cap (so breadth is never the limiter) so the ONLY thing
that differs is depth_bias: the BIASED world keeps connected DEPTH climbing across the WHOLE horizon (still
deepening on the very last tick) while the UNBIASED world (R174 regime, identical cap + tick count) PLATEAUS
its depth by mid-horizon. A sustained-depth-vs-plateau split is the depth-pressure signature, not a cap or
run-length artifact — both run the same K and the same number of ticks.

Two modes (mirrors run_genesis_r174.py):
  tick <state_dir> <seed> <seg_steps> <bias>   run ONE tick as a GENUINE separate process: resume the world
                                               from disk, climb one segment.
  (no args)                                    full REAL-VERIFY: drive the biased AND unbiased climbs as REAL
                                               subprocess ticks, confirm biased keeps deepening while unbiased
                                               plateaus, render runs/r175_depth/{depth.png,world.gif}.
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

OUT = "runs/r175_depth"


def r175_cfg(depth_bias, K=20000):
    """The R174 SUSTAINED-climb regime (large cap, gentle innovation, deep gates) + the ONE knob depth_bias.
    The biased-vs-unbiased control changes depth_bias ALONE — same cap K, same everything else."""
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=2, n_food_tiers=8, recipe_level_step=2,
        n_capabilities=4, cap_level_step=3, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40, depth_bias=depth_bias)


def tick_mode(state_dir, seed, seg, bias):
    r = daemon.tick(state_dir, r175_cfg(bias), seed=seed, segment_steps=seg, log_every=20)
    tr = persist.load_trajectory(state_dir)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    print(f"  [pid {os.getpid()}] bias={bias} tick {r['tick_index']} {tag} steps {r['start_step']}->{r['end_step']} | "
          f"depth {tr['conn_depth'][-1]:.0f} breadth {tr['breadth'][-1]:.0f} "
          f"edible {tr['edible_tiers'][-1]:.2f} axes {tr['realized_axes'][-1]:.2f} pop {tr['population'][-1]:.0f}",
          flush=True)


def drive_real_ticks(tag, state_dir, seed, seg, n_ticks, bias):
    """Drive `n_ticks` ticks as REAL separate subprocesses (genuine process death between every tick)."""
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    print(f"--- {tag}: {n_ticks} REAL subprocess ticks, depth_bias={bias} ({state_dir}) ---", flush=True)
    for _ in range(n_ticks):
        subprocess.run([sys.executable, os.path.abspath(__file__), "tick", state_dir,
                        str(seed), str(seg), str(bias)], check=True)
    tr = persist.load_trajectory(state_dir)
    ends = np.where(tr["step"] % seg == 0)[0][1:]      # one last-of-segment sample per tick
    return {k: tr[v][ends] for k, v in
            (("tick", "step"), ("step", "step"), ("conn_depth", "conn_depth"), ("breadth", "breadth"),
             ("edible_tiers", "edible_tiers"), ("realized_axes", "realized_axes"), ("population", "population"))}


def render_world(state_dir, seed, bias):
    """Render the developed open-ended civilization (violet->gold by cultural depth) — watchable proof the
    depth-biased climb produced a deep, alive population, not a frozen or collapsed one."""
    from alife.render3d import Renderer3D
    cfg = r175_cfg(bias)
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    w.load_checkpoint(os.path.join(state_dir, "checkpoint.npz"))
    print(f"  render: restored tree.n={w._tree.n} diet_ceiling={w.diet_capability_ceiling()}", flush=True)
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


def render_depth_panel(bias_curve, unb_curve, path, title):
    """2x2 depth-biased-vs-unbiased per-tick climb. Reuse render_climb_panel's pure form but relabel for the
    DEPTH control (biased keeps deepening; unbiased plateaus)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    panels = (("conn_depth", "connected tech DEPTH (the R175 target)"),
              ("breadth", "society repertoire BREADTH"),
              ("edible_tiers", "embodied DIET ceiling (body)"),
              ("realized_axes", "embodied capability AXES (body)"))
    bt, ut = np.asarray(bias_curve["tick"]), np.asarray(unb_curve["tick"])
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle(title, fontsize=13)
    for a, (key, sub) in zip(ax.flat, panels):
        a.plot(bt, np.asarray(bias_curve[key]), color="#1f77b4", lw=2.2, marker="o", ms=4,
               label="depth-biased (depth_bias=1.0)")
        a.plot(ut, np.asarray(unb_curve[key]), color="#d62728", lw=2.2, marker="s", ms=4, ls="--",
               label="unbiased (depth_bias=0 = R174) — depth plateaus")
        a.set_title(sub, fontsize=10)
        a.set_xlabel("unattended tick")
        a.grid(alpha=0.25)
        a.legend(fontsize=8, loc="best")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return int(bt.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    seed, n_ticks, seg = 0, 10, 60
    half = n_ticks // 2
    t0 = time.time()

    bias = drive_real_ticks("DEPTH-BIASED", os.path.join(OUT, "bias"), seed, seg, n_ticks, 1.0)
    unb = drive_real_ticks("UNBIASED control (R174)", os.path.join(OUT, "unb"), seed, seg, n_ticks, 0.0)

    # the falsifiable verdict (same checks as the unit test, on genuine separate-process histories)
    biased_climbs_late = bool(bias["conn_depth"][-1] > bias["conn_depth"][half] + 5)
    biased_still_deepening = bool(bias["conn_depth"][-1] - bias["conn_depth"][-2] >= 1)
    unbiased_plateaus = bool(unb["conn_depth"][-1] - unb["conn_depth"][half] <= 2
                             and unb["conn_depth"][-1] - unb["conn_depth"][-2] <= 1)
    biased_far_deeper = bool(bias["conn_depth"][-1] > 3 * unb["conn_depth"][-1])
    body_ok = bool(bias["edible_tiers"][-1] >= unb["edible_tiers"][-1])
    alive = bool(bias["population"][-1] >= 500 and unb["population"][-1] >= 500)

    print(f"\n  BIASED depth/tick:   {' '.join(f'{d:.0f}' for d in bias['conn_depth'])}  "
          f"edible {bias['edible_tiers'][0]:.0f}->{bias['edible_tiers'][-1]:.0f}", flush=True)
    print(f"  UNBIAS depth/tick:   {' '.join(f'{d:.0f}' for d in unb['conn_depth'])}", flush=True)
    print(f"  BIASED breadth/tick: {' '.join(f'{b:.0f}' for b in bias['breadth'])}", flush=True)
    print(f"  VERDICT: biased_climbs_late={biased_climbs_late} biased_still_deepening={biased_still_deepening} "
          f"unbiased_plateaus={unbiased_plateaus} biased_far_deeper={biased_far_deeper} "
          f"body_ok={body_ok} alive={alive}", flush=True)

    render_depth_panel(bias, unb, os.path.join(OUT, "depth.png"),
                       title=f"R175 GENESIS — SUSTAINED DEPTH across {n_ticks} real process ticks: "
                             f"depth-biased keeps deepening vs unbiased (R174) plateaus")
    nfr = render_world(os.path.join(OUT, "bias"), seed, 1.0)

    ok = (biased_climbs_late and biased_still_deepening and unbiased_plateaus and biased_far_deeper
          and body_ok and alive)
    print(f"\nwrote {OUT}/depth.png + world.gif ({nfr} frames) in {time.time()-t0:.1f}s | PASS={ok}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tick":
        tick_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]))
    else:
        main()
