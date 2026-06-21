"""R170 REAL-VERIFY — open-endedness made CAUSAL in the LIVE world.

Runs the full-stack living GenesisWorld with the GENERATIVE tech tree (combinatorial.GrowingTree, grown
on demand from the population's real compositions) and shows that the living culture's frontier keeps
climbing, bounded ONLY by the capacity cap:

  - GENERATIVE big-cap (max_techniques=4000): breadth + depth keep climbing with run length.
  - GENERATIVE capped   (max_techniques=30)  : the SAME machinery FREEZES once the tree is full.
  - FIXED pre-built tree (generative_tree=False, max_techniques=4000): a frozen pre-set ceiling, the
    frontier cannot pass the random tree's deepest level no matter how long it runs.

Outputs runs/r170_generative/{panel.png, world.gif}. panel = the three frontier trajectories measured
from the LIVING population each step; world.gif = the developed generative civilization, agents coloured
violet->gold by their culture DEPTH. Single foreground run, no background tasks.
"""

from __future__ import annotations

import os
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.civdev import civ_config
from alife.genesis.genesis import GenesisWorld

OUT = "runs/r170_generative"
_LOCKED = np.array([0.42, 0.13, 0.62])    # violet (shallow culture)
_UNLOCKED = np.array([1.0, 0.80, 0.10])   # gold   (deep culture)


def _gen_cfg(max_techniques: int, generative: bool):
    # full-stack viable world WITHOUT the fixed-deep-node gates (incompatible with the generative tree),
    # but WITH building + cumulative combinatorial culture. Lighter than civ_config for a fast verify.
    return civ_config(
        tech_actions=False, tech_capabilities=False,
        generative_tree=generative, max_techniques=max_techniques, innov_steps=3,
        n0=300, capacity=1000, food_cap=600, food_regrow=40,
    )


def _depth_color(world: GenesisWorld) -> np.ndarray:
    act = world.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    t = world.pop.tech[act]
    frac = (t / max(float(t.max()), 1.0))[:, None]
    return _LOCKED * (1.0 - frac) + _UNLOCKED * frac


def run(world: GenesisWorld, steps: int, every: int = 10):
    T, BR, ML, TN = [], [], [], []
    for s in range(steps):
        world.step()
        if s % every:
            continue
        out = world.combinatorial_test()
        if not out:
            continue
        T.append(s)
        BR.append(out["pop_distinct"])
        ML.append(out["max_level"])
        TN.append(world._tree.n if world._tree is not None else None)
    return dict(step=np.array(T), breadth=np.array(BR), max_level=np.array(ML), tree_n=TN)


def render_gif(world: GenesisWorld, frames: int = 30):
    from alife.render3d import Renderer3D
    r = Renderer3D(world.cfg.world, width=480, height=360)
    imgs = []
    for i in range(frames):
        world.step()
        act = world.pop.active()
        if act.size:
            imgs.append(r.render(world.pop.pos[act], world.pop.vel[act], _depth_color(world),
                                 cam_angle=i * 0.14, cam_elev=0.42, food=world.food))
    r.ctx.release()
    if imgs:
        import imageio
        imageio.mimsave(os.path.join(OUT, "world.gif"), imgs, fps=12, loop=0)
    return len(imgs), (imgs[-1] if imgs else None)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    steps = 320
    big = GenesisWorld(_gen_cfg(4000, generative=True), seed=1, evolve=True)
    cap = GenesisWorld(_gen_cfg(30, generative=True), seed=1, evolve=True)
    fix = GenesisWorld(_gen_cfg(4000, generative=False), seed=1, evolve=True)
    print("running 3 live worlds x", steps, "steps ...")
    rb = run(big, steps)
    rc = run(cap, steps)
    rf = run(fix, steps)
    print(f"big: breadth {rb['breadth'][0]}->{rb['breadth'][-1]} depth {rb['max_level'][0]}->{rb['max_level'][-1]} "
          f"tree_n->{big._tree.n}")
    print(f"cap: breadth {rc['breadth'][0]}->{rc['breadth'][-1]} depth {rc['max_level'][0]}->{rc['max_level'][-1]} "
          f"tree_n->{cap._tree.n}")
    print(f"fix: breadth {rf['breadth'][0]}->{rf['breadth'][-1]} depth {rf['max_level'][0]}->{rf['max_level'][-1]} "
          f"(fixed pre-built tree, frozen ceiling)")

    nfr, last = render_gif(big, frames=30)

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("R170 — open-endedness made CAUSAL in the living world: the generative tech tree grows "
                 "from the population's real compositions", fontsize=12)
    ax[0, 0].plot(rb["step"], rb["breadth"], "-", color="#d4a017", lw=2.2, label="generative big-cap (K=4000)")
    ax[0, 0].plot(rf["step"], rf["breadth"], "--", color="#3b7dd8", lw=2.0, label="fixed pre-built tree (K=4000)")
    ax[0, 0].plot(rc["step"], rc["breadth"], "-", color="#c0392b", lw=2.0, label="generative capped (K=30)")
    ax[0, 0].set_title("cultural BREADTH (distinct techniques known by the living pop)")
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("pop_distinct"); ax[0, 0].legend(fontsize=8)

    ax[0, 1].plot(rb["step"], rb["max_level"], "-", color="#d4a017", lw=2.2, label="generative big-cap")
    ax[0, 1].plot(rf["step"], rf["max_level"], "--", color="#3b7dd8", lw=2.0, label="fixed pre-built tree")
    ax[0, 1].plot(rc["step"], rc["max_level"], "-", color="#c0392b", lw=2.0, label="generative capped (K=30)")
    ax[0, 1].set_title("frontier DEPTH (deepest tech level in the living pop)")
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylabel("max_level"); ax[0, 1].legend(fontsize=8)

    tn_big = [x for x in rb["tree_n"] if x is not None]
    tn_cap = [x for x in rc["tree_n"] if x is not None]
    ax[1, 0].plot(rb["step"][:len(tn_big)], tn_big, "-", color="#d4a017", lw=2.2, label="generative big-cap")
    ax[1, 0].plot(rc["step"][:len(tn_cap)], tn_cap, "-", color="#c0392b", lw=2.0, label="generative capped (K=30)")
    ax[1, 0].axhline(30, color="#c0392b", ls=":", lw=1.0)
    ax[1, 0].set_title("MATERIALIZED tree size (nodes grown on demand) — capped freezes at K=30")
    ax[1, 0].set_xlabel("step"); ax[1, 0].set_ylabel("tree nodes"); ax[1, 0].legend(fontsize=8)

    if last is not None:
        ax[1, 1].imshow(last)
        ax[1, 1].set_title(f"developed generative civilization (violet->gold = culture depth), {nfr} frames")
    ax[1, 1].axis("off")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=110)
    print(f"wrote {OUT}/panel.png + world.gif ({nfr} frames) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
