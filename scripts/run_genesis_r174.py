"""R174 — GENESIS: the SUSTAINED multi-day climb. The world that KEEPS developing, not just persists.

R173 stood up the unattended tick loop, but with a small tree cap the climb SATURATED inside tick 1 — so
"leave it running for days and it keeps developing" was hollow past the first tick. R174 fixes the regime
(not the mechanism): a LARGE memory cap + gentler innovation give the open-ended tree headroom to keep
climbing tick after tick, and DEEPER diet/capability gates make the EMBODIED ceiling (what the body can
eat / do) keep rising with the depth instead of maxing out at once.

THE FALSIFIABLE HEADLINE — the open-ended-vs-capped CONTROL, driven as GENUINE separate-process ticks
(true process death between every tick): the OPEN-ENDED world (large cap) keeps climbing across the WHOLE
horizon — breadth still rising in the final tick, and the connected DEPTH and the embodied DIET/AXES ceilings
end strictly higher than they began (the body keeps developing) — while the CAPPED world (small cap,
otherwise identical machinery) FREEZES once its tree is full. The only difference is the cap, so a
sustained-vs-frozen split is the open-endedness signature, not merely "ran longer".

Two modes (mirrors run_genesis_r173.py):
  tick <state_dir> <seed> <seg_steps> <K>   run ONE unattended tick as a GENUINE separate process: resume
                                            the world from disk, climb one segment, refresh live_panel.png.
  (no args)                                 full REAL-VERIFY: drive the open-ended AND capped climbs as REAL
                                            subprocess ticks, confirm open-ended keeps climbing while capped
                                            freezes, render runs/r174_climb/{climb.png,world.gif}.
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

OUT = "runs/r174_climb"


def r174_cfg(K, n_food_tiers=8, n_caps=4):
    """SUSTAINED-climb regime (== tests._r174_cfg). The ONLY knob the capped control changes is K."""
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=2, n_food_tiers=n_food_tiers, recipe_level_step=2,
        n_capabilities=n_caps, cap_level_step=3, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def tick_mode(state_dir, seed, seg, K):
    r = daemon.tick(state_dir, r174_cfg(K), seed=seed, segment_steps=seg, log_every=20)
    tr = persist.load_trajectory(state_dir)
    tag = "BOOTSTRAP" if r["bootstrap"] else "RESUME"
    print(f"  [pid {os.getpid()}] K={K} tick {r['tick_index']} {tag} steps {r['start_step']}->{r['end_step']} | "
          f"depth {tr['conn_depth'][-1]:.0f} breadth {tr['breadth'][-1]:.0f} "
          f"edible {tr['edible_tiers'][-1]:.2f} axes {tr['realized_axes'][-1]:.2f} pop {tr['population'][-1]:.0f}",
          flush=True)


def drive_real_ticks(tag, state_dir, seed, seg, n_ticks, K):
    """Drive `n_ticks` ticks as REAL separate subprocesses (genuine process death between every tick).
    Returns the per-tick climb curve read from the accumulated on-disk trajectory."""
    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)
    print(f"--- {tag}: {n_ticks} REAL subprocess ticks, K={K} ({state_dir}) ---", flush=True)
    for _ in range(n_ticks):
        subprocess.run([sys.executable, os.path.abspath(__file__), "tick", state_dir,
                        str(seed), str(seg), str(K)], check=True)
    tr = persist.load_trajectory(state_dir)
    # one last-of-segment sample per tick: every step is a multiple of seg at tick ends
    ends = np.where(tr["step"] % seg == 0)[0][1:]      # indices at step seg,2*seg,... (skip step 0)
    return {k: tr[v][ends] for k, v in
            (("tick", "step"), ("step", "step"), ("conn_depth", "conn_depth"), ("breadth", "breadth"),
             ("edible_tiers", "edible_tiers"), ("realized_axes", "realized_axes"), ("population", "population"))}


def render_world(state_dir, seed, K):
    """Render the developed open-ended civilization (violet->gold by cultural depth) — watchable proof the
    sustained climb produced a deep, alive population, not a frozen or collapsed one."""
    from alife.render3d import Renderer3D
    cfg = r174_cfg(K)
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


def main():
    os.makedirs(OUT, exist_ok=True)
    seed, n_ticks, seg = 0, 8, 60
    K_OPEN, K_CAP = 20000, 250
    t0 = time.time()

    op = drive_real_ticks("OPEN-ENDED", os.path.join(OUT, "open"), seed, seg, n_ticks, K_OPEN)
    cap = drive_real_ticks("CAPPED control", os.path.join(OUT, "capped"), seed, seg, n_ticks, K_CAP)

    # the falsifiable verdict (same checks as the unit test, on genuine separate-process histories)
    half = n_ticks // 2
    open_still_climbing = bool(op["breadth"][-1] > op["breadth"][half] and op["breadth"][-1] - op["breadth"][-2] >= 50)
    body_developed = bool(op["edible_tiers"][-1] > op["edible_tiers"][0] and op["realized_axes"][-1] > op["realized_axes"][0]
                          and op["conn_depth"][-1] > op["conn_depth"][0])
    capped_frozen = bool(cap["breadth"][-1] - cap["breadth"][-2] <= 3)
    open_far_past = bool(op["breadth"][-1] > 10 * cap["breadth"][-1] and op["conn_depth"][-1] > cap["conn_depth"][-1])
    alive = bool(op["population"][-1] >= 500 and cap["population"][-1] >= 200)

    print(f"\n  OPEN  breadth/tick: {' '.join(f'{b:.0f}' for b in op['breadth'])}", flush=True)
    print(f"  OPEN  depth/tick:   {' '.join(f'{d:.0f}' for d in op['conn_depth'])}  "
          f"edible {op['edible_tiers'][0]:.0f}->{op['edible_tiers'][-1]:.0f}  "
          f"axes {op['realized_axes'][0]:.0f}->{op['realized_axes'][-1]:.0f}", flush=True)
    print(f"  CAP   breadth/tick: {' '.join(f'{b:.0f}' for b in cap['breadth'])}  "
          f"depth {cap['conn_depth'][-1]:.0f}", flush=True)
    print(f"  VERDICT: open_still_climbing={open_still_climbing} body_developed={body_developed} "
          f"capped_frozen={capped_frozen} open_far_past={open_far_past} alive={alive}", flush=True)

    # the headline figure: open-ended vs capped per-tick climb, eye-checkable
    daemon.render_climb_panel(op, cap, os.path.join(OUT, "climb.png"),
                              title=f"R174 GENESIS — SUSTAINED CLIMB across {n_ticks} real process ticks: "
                                    f"open-ended (K={K_OPEN}) keeps developing vs capped (K={K_CAP}) freezes")
    nfr = render_world(os.path.join(OUT, "open"), seed, K_OPEN)

    ok = open_still_climbing and body_developed and capped_frozen and open_far_past and alive
    print(f"\nwrote {OUT}/climb.png + world.gif ({nfr} frames) in {time.time()-t0:.1f}s | PASS={ok}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tick":
        tick_mode(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
    else:
        main()
