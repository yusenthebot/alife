"""R177 — GENESIS: CUMULATIVE-CULTURE BODY. Drive embodiment off ACCESSIBLE BANKED culture, not personal mastery.

R176 made the body CONTINUOUS (speed/reach scale smoothly with cultural depth), but its DRIVER — the agent's
PERSONAL realized depth (pop.tech) — SATURATES at the innovation/transmission-loss equilibrium (R176 caveat 2):
each generation copies parent+hearth at fidelity<1 then adds only innov_steps, so the living-pop MEAN depth settles
to an asymptote and the body's climb decelerates. R177 adds `pheno_cumulative`: the body's driver becomes the
ACCESSIBLE ACCUMULATED culture = max(personal pop.tech, the deepest record BANKED in the nearest strong hearth the
agent can reach). The banked hearth record (struct_tech) is written by a running MAX over every builder ever (a
lossless EXTERNAL social memory — Boyd/Richerson: societies store culture better than any individual remembers it),
so it RATCHETS and never saturates the way lossy individual mastery does. The body keeps deepening with the
SOCIETY's cumulative culture — the Stage-4/5 niche-construction feedback of the built world back into embodiment.
pheno_cumulative=False is byte-identical to R176 (driver stays pop.tech, no KD-query, no extra RNG).

THE FALSIFIABLE HEADLINE — driven as GENUINE separate-process ticks (true process death between every tick), at the
R175/R176 SUSTAINED-DEPTH regime, the CUMULATIVE-culture body (driver = banked record, a ratchet) ends DEEPER and
keeps rising where the R176 PERSONAL-mastery body (driver = saturating living-pop mean) decelerates — the ONLY knob
that differs is pheno_cumulative. Within the cumulative run the body's actual driver depth rises ABOVE the personal-
mastery baseline it would otherwise be stuck at (banked > personal). gain=0 stays frozen at 1.0 (the mapping, not a
relabel of depth).

Two modes (mirrors run_genesis_r176.py):
  tick <state_dir> <seed> <seg_steps> <cum> <gain>   run ONE tick as a GENUINE separate process: resume, climb one
                                                     segment. cum in {0,1} selects personal(R176)/cumulative(R177).
  (no args)                                          full REAL-VERIFY: drive the cumulative AND personal arms as REAL
                                                     subprocess ticks, confirm the cumulative body outclimbs personal
                                                     mastery, render runs/r177_body/{body.png,world.gif}.
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
from dataclasses import replace

OUT = "runs/r177_body"


def r177_cfg(cum, gain, K=20000):
    """R176's SUSTAINED-DEPTH regime + the R177 cumulative-culture body. The cumulative-vs-personal arm changes
    pheno_cumulative ALONE (both depth_phenotype=True, same gain) — same depth-climbing world underneath."""
    base = civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        depth_phenotype=True, pheno_speed_gain=gain, pheno_reach_gain=gain,
        max_techniques=K, innov_steps=2, n_food_tiers=8, recipe_level_step=2,
        n_capabilities=4, cap_level_step=3, tier0_frac=0.4, depth_bias=1.0,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)
    return replace(base, pheno_cumulative=bool(cum))


def tick_mode(state_dir, seed, seg, cum, gain):
    r = daemon.tick(state_dir, r177_cfg(cum, gain), seed=seed, segment_steps=seg, log_every=20)
    tr = persist.load_trajectory(state_dir)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    print(f"  [pid {os.getpid()}] cum={cum} tick {r['tick_index']} {tag} steps {r['start_step']}->{r['end_step']} | "
          f"depth {tr['conn_depth'][-1]:.0f} body_scale {tr['embodied_scale'][-1]:.3f} "
          f"driver {tr['body_driver_depth'][-1]:.1f} personal {tr['personal_depth'][-1]:.1f} "
          f"pop {tr['population'][-1]:.0f}", flush=True)


def drive_real_ticks(tag, state_dir, seed, seg, n_ticks, cum, gain):
    """Drive `n_ticks` ticks as REAL separate subprocesses (genuine process death between every tick)."""
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    print(f"--- {tag}: {n_ticks} REAL subprocess ticks, cum={cum} gain={gain} ({state_dir}) ---", flush=True)
    for _ in range(n_ticks):
        subprocess.run([sys.executable, os.path.abspath(__file__), "tick", state_dir,
                        str(seed), str(seg), str(cum), str(gain)], check=True)
    tr = persist.load_trajectory(state_dir)
    ends = np.where(tr["step"] % seg == 0)[0][1:]      # one last-of-segment sample per tick
    keys = ("step", "conn_depth", "breadth", "edible_tiers", "realized_axes", "embodied_scale",
            "body_driver_depth", "personal_depth", "population")
    return {k: tr[k][ends] for k in keys}


def render_world(state_dir, seed, cum, gain):
    """Render the developed cumulative-culture civilization (violet->gold by cultural depth) — watchable proof the
    body-deepening produced a deep, alive population, not a frozen or collapsed one."""
    from alife.render3d import Renderer3D
    cfg = r177_cfg(cum, gain)
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    w.load_checkpoint(os.path.join(state_dir, "checkpoint.npz"))
    es = w.embodied_scale()
    print(f"  render: restored tree.n={w._tree.n} body_scale={es['mean_speed_mult']:.3f} "
          f"driver={es['mean_depth']:.1f} personal={es['mean_personal_depth']:.1f} "
          f"n_hearths={w._strong_hearths().size}", flush=True)
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


def render_body_panel(cum, per, path, title):
    """2x2 cumulative-vs-personal per-tick climb. Headline: embodied_scale (cumulative outclimbs personal); the
    driver-vs-personal gap WITHIN the cumulative run (banked ratchet > saturating mastery); conn_depth climbs in
    BOTH (shared driver); population alive in both."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = np.arange(1, cum["embodied_scale"].size + 1)
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle(title, fontsize=12)

    a = ax[0, 0]
    a.plot(n, cum["embodied_scale"], color="#1f77b4", lw=2.4, marker="o", ms=4, label="pheno_cumulative (banked, R177)")
    a.plot(n, per["embodied_scale"], color="#ff7f0e", lw=2.4, marker="s", ms=4, ls="--", label="personal mastery (R176)")
    a.set_title("CONTINUOUS body: mean speed mult — cumulative outclimbs personal", fontsize=9)

    a = ax[0, 1]
    a.plot(n, cum["body_driver_depth"], color="#2ca02c", lw=2.4, marker="o", ms=4, label="body DRIVER = banked record (ratchet)")
    a.plot(n, cum["personal_depth"], color="#d62728", lw=2.4, marker="s", ms=4, ls="--", label="personal mastery (saturates)")
    a.set_title("WITHIN the cumulative run: banked driver rises above personal mastery", fontsize=9)

    a = ax[1, 0]
    a.plot(n, cum["conn_depth"], color="#9467bd", lw=2.4, marker="o", ms=4, label="cumulative arm")
    a.plot(n, per["conn_depth"], color="#8c564b", lw=2.4, marker="s", ms=4, ls="--", label="personal arm")
    a.set_title("connected tech DEPTH (the shared driver climbs in both)", fontsize=9)

    a = ax[1, 1]
    a.plot(n, cum["population"], color="#1f77b4", lw=2.4, marker="o", ms=4, label="cumulative arm")
    a.plot(n, per["population"], color="#ff7f0e", lw=2.4, marker="s", ms=4, ls="--", label="personal arm")
    a.set_title("living population (both healthy)", fontsize=9)

    for a in ax.flat:
        a.set_xlabel("unattended tick")
        a.grid(alpha=0.25)
        a.legend(fontsize=8, loc="best")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return int(n.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    seed, n_ticks, seg, gain = 0, 8, 50, 0.02
    t0 = time.time()

    cum = drive_real_ticks("CUMULATIVE-CULTURE body (banked record)", os.path.join(OUT, "cum"), seed, seg, n_ticks, 1, gain)
    per = drive_real_ticks("PERSONAL-mastery body (R176)", os.path.join(OUT, "per"), seed, seg, n_ticks, 0, gain)

    # the falsifiable verdict (same family as the unit test, on genuine separate-process histories)
    driver_beats_personal = bool(cum["body_driver_depth"][-1] > cum["personal_depth"][-1] + 1.0)
    cum_outclimbs_personal = bool(cum["embodied_scale"][-1] > per["embodied_scale"][-1])
    cum_still_rising = bool(cum["embodied_scale"][-1] - cum["embodied_scale"][-2] > 0.0)
    depth_climbs_both = bool(cum["conn_depth"][-1] > cum["conn_depth"][0] + 10
                             and per["conn_depth"][-1] > per["conn_depth"][0] + 10)
    alive = bool(cum["population"][-1] >= 400 and per["population"][-1] >= 400)

    print(f"\n  CUM body_scale/tick:  {' '.join(f'{d:.3f}' for d in cum['embodied_scale'])}", flush=True)
    print(f"  CUM driver/tick:      {' '.join(f'{d:.1f}' for d in cum['body_driver_depth'])}", flush=True)
    print(f"  CUM personal/tick:    {' '.join(f'{d:.1f}' for d in cum['personal_depth'])}", flush=True)
    print(f"  PER body_scale/tick:  {' '.join(f'{d:.3f}' for d in per['embodied_scale'])}", flush=True)
    print(f"  PER personal/tick:    {' '.join(f'{d:.1f}' for d in per['personal_depth'])}", flush=True)
    print(f"  CUM depth/tick:       {' '.join(f'{d:.0f}' for d in cum['conn_depth'])}", flush=True)
    print(f"  VERDICT: driver_beats_personal={driver_beats_personal} cum_outclimbs_personal={cum_outclimbs_personal} "
          f"cum_still_rising={cum_still_rising} depth_climbs_both={depth_climbs_both} alive={alive}", flush=True)

    render_body_panel(cum, per, os.path.join(OUT, "body.png"),
                      title=f"R177 GENESIS — CUMULATIVE-CULTURE BODY across {n_ticks} real process ticks: embodiment "
                            f"driven by ACCESSIBLE BANKED culture (a ratchet) outclimbs PERSONAL mastery (saturates)")
    nfr = render_world(os.path.join(OUT, "cum"), seed, 1, gain)

    ok = (driver_beats_personal and cum_outclimbs_personal and depth_climbs_both and alive)
    print(f"\nwrote {OUT}/body.png + world.gif ({nfr} frames) in {time.time()-t0:.1f}s | PASS={ok}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tick":
        tick_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6]))
    else:
        main()
