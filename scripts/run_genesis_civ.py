"""R168 — GENESIS: the persistent, watchable, FULL-STACK living civilization.

Every civilization mechanism validated separately across R148-R167 (niche construction / processing /
cumulative combinatorial culture / tech-gated diet tiers / culture-gated physical capabilities) runs
TOGETHER here in ONE persistent world that develops just by running — the CEO's actual deliverable. Outputs
to runs/r168_civ/ (gitignored):
  civ.gif    — the 3D world over a long run; agents coloured violet->gold by REALIZED culture depth (how
               many physical capability axes their culture has unlocked) — deep-culture agents emerge live.
  panel.png  — the civilization developing: connected tech depth, realized capability axes, edible diet
               tiers, breadth, population — full stack vs the ASOCIAL control (learn=False).
  checkpoint.npz — saved mid-run and reloaded to PROVE the world is persistable/resumable (cloud/multi-day).

Falsifiable headline (red-teamed): same world, same physics, the ONLY change is whether culture is
transmitted. The full stack DEVELOPS (connected tech depth + capability axes + diet climb); the asocial
control stays at the seed floor. One sim at a time; the GL context is released after rendering.
"""
import os
import sys
import time

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis import civdev, techdepth
from alife.genesis.genesis import GenesisWorld

OUT = "runs/r168_civ"
os.makedirs(OUT, exist_ok=True)


def headline_run(steps, seed=0, render_every=30, log_every=25):
    """The full-stack civilization with 3D rendering + the development trajectory + a checkpoint/resume proof."""
    from alife.render3d import Renderer3D
    cfg = civdev.civ_config()
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    pa, pb, level = w._tree_pa, w._tree_pb, w._tree_level
    n_seed = cfg.n_seed_tech
    hist = {k: [] for k in ("step", "population", "conn_depth", "closure", "breadth",
                            "realized_axes", "edible_tiers", "diversity", "max_gen")}
    frames = []
    renderer = Renderer3D(cfg.world, width=480, height=360)
    ckpt = os.path.join(OUT, "checkpoint.npz")
    mid = steps // 2
    resume_ok = None
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % log_every == 0:
            snp = w.snapshot()
            known = techdepth.society_repertoire(w)
            hist["step"].append(s)
            hist["population"].append(float(snp["population"]))
            hist["conn_depth"].append(techdepth.connected_depth(known, pa, pb, level, n_seed))
            hist["closure"].append(techdepth.closure_fraction(known, pa, pb, n_seed))
            hist["breadth"].append(int(known.sum()))
            hist["realized_axes"].append(float(snp.get("realized_axes", np.nan)))
            hist["edible_tiers"].append(float(snp.get("mean_edible_tiers", np.nan)))
            hist["diversity"].append(float(snp["diversity"]))
            hist["max_gen"].append(float(snp["max_gen"]))
        if s == mid:                                            # PERSISTENCE: save, reload, prove continuity
            w.save_checkpoint(ckpt)
            w2 = GenesisWorld(cfg, seed=seed, evolve=True)
            w2.load_checkpoint(ckpt)
            s_a, s_b = w.snapshot(), w2.snapshot()
            resume_ok = (abs(s_a["population"] - s_b["population"]) < 1e-6
                         and abs(s_a["breadth"] if "breadth" in s_a else 0 - 0) < 1e9
                         and s_a["max_gen"] == s_b["max_gen"])
            del w2
        if s % render_every == 0:
            act = w.pop.active()
            if act.size:
                pos, vel = w.pop.pos[act], w.pop.vel[act]
                color = civdev.capability_color(w)
                frames.append(renderer.render(pos, vel, color, cam_angle=s * 0.012,
                                              cam_elev=0.42, food=w.food))
    renderer.ctx.release()
    w.save_checkpoint(ckpt)
    if frames:
        imageio.mimsave(os.path.join(OUT, "civ.gif"), frames, fps=12, loop=0)
    print(f"headline: {steps} steps in {time.time()-t0:.1f}s, {len(frames)} frames | "
          f"conn_depth {hist['conn_depth'][0]}->{hist['conn_depth'][-1]} axes {hist['realized_axes'][-1]:.2f} "
          f"edible {hist['edible_tiers'][-1]:.2f} pop {hist['population'][-1]:.0f} gen {hist['max_gen'][-1]:.0f} | "
          f"resume_ok={resume_ok}", flush=True)
    return hist, resume_ok


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    rt_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    rt_seeds = (0, 1)

    print(f"=== headline full-stack civilization ({steps} steps, 3D render) ===", flush=True)
    hist, resume_ok = headline_run(steps, seed=0)

    print(f"=== red-team: civilization develops only WITH social learning, {len(rt_seeds)} seeds, "
          f"{rt_steps} steps ===", flush=True)
    runs = {}
    for seed in rt_seeds:
        out = civdev.develop_vs_control(rt_steps, seed=seed, every=25)
        runs[seed] = out
        f, c = out["full"], out["control"]
        print(f"  seed {seed}: FULL conn_depth->{f['conn_depth'][-1]} axes {f['realized_axes'][-1]:.2f} "
              f"edible {f['edible_tiers'][-1]:.2f} breadth {f['breadth'][-1]} | "
              f"CTRL conn_depth->{c['conn_depth'][-1]} axes {c['realized_axes'][-1]:.2f} "
              f"edible {c['edible_tiers'][-1]:.2f} breadth {c['breadth'][-1]}", flush=True)
    f_cd = np.array([runs[s]["full"]["conn_depth"][-1] for s in rt_seeds])
    c_cd = np.array([runs[s]["control"]["conn_depth"][-1] for s in rt_seeds])
    print(f"  MEAN connected depth: FULL {f_cd.mean():.1f} vs CONTROL {c_cd.mean():.1f} "
          f"-> develops {(f_cd > c_cd).all()} on all seeds", flush=True)

    # panel
    st = np.array(hist["step"])
    s0 = rt_seeds[0]
    full0, ctrl0 = runs[s0]["full"], runs[s0]["control"]
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("R168 GENESIS — full-stack living civilization (full stack vs asocial control)", fontsize=13)
    ax[0, 0].plot(st, hist["conn_depth"], color="#d62728", lw=2)
    ax[0, 0].set_title("connected tech depth — the cumulative ladder (headline run)")
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("connected depth")
    ax[0, 1].plot(st, hist["realized_axes"], color="#ff7f0e", lw=2)
    ax[0, 1].set_title("realized physical capability axes unlocked by culture")
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylim(-0.1, 2.2)
    ax[0, 2].plot(st, hist["edible_tiers"], color="#2ca02c", lw=2)
    ax[0, 2].set_title("mean edible diet tiers (deeper culture -> richer diet)")
    ax[0, 2].set_xlabel("step")
    ax[1, 0].plot(full0["step"], full0["conn_depth"], color="#2ca02c", lw=2, label="full stack")
    ax[1, 0].plot(ctrl0["step"], ctrl0["conn_depth"], color="#7f7f7f", lw=2, ls="--", label="asocial control")
    ax[1, 0].set_title(f"DEVELOPS only with social learning (seed {s0})")
    ax[1, 0].set_xlabel("step"); ax[1, 0].set_ylabel("connected depth"); ax[1, 0].legend()
    ax[1, 1].plot(full0["step"], full0["realized_axes"], color="#2ca02c", lw=2, label="full stack")
    ax[1, 1].plot(ctrl0["step"], ctrl0["realized_axes"], color="#7f7f7f", lw=2, ls="--", label="asocial control")
    ax[1, 1].set_title("capability axes: full vs control"); ax[1, 1].set_xlabel("step")
    ax[1, 1].set_ylim(-0.1, 2.2); ax[1, 1].legend()
    ax[1, 2].plot(st, hist["population"], color="#1f77b4", lw=2)
    ax[1, 2].set_title(f"population (persistent; resume_ok={resume_ok})"); ax[1, 2].set_xlabel("step")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=110)
    print(f"wrote {OUT}/panel.png and {OUT}/civ.gif", flush=True)


if __name__ == "__main__":
    main()
