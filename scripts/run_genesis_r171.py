"""R171 REAL-VERIFY — the open-ended grown tree CAUSALLY drives EMBODIED capability.

R170 made the cultural REPERTOIRE open-ended (the grown tree's depth climbs with the cap, freezes when
capped). R171 makes that open-endedness CAUSAL on the body: under depth_gates the diet tiers an agent can
physically eat and the locomotion/reach axes it has unlocked are gated on its REALIZED cultural depth
(pop.tech). So the embodied diet/capability CEILING inherits the tree's open-endedness:

  - UNCAPPED (max_techniques=4000): culture depth climbs -> the population progressively unlocks deeper diet
    tiers and both capability axes; it physically EATS across all tiers.
  - CAPPED   (max_techniques=20)  : the SAME machinery freezes the tree's depth -> the embodied ceiling is
    frozen at the free tier 0 / no axes; the population can NEVER eat a locked tier.
  - NULL (uncapped, innov_steps=0): no compositions -> the tree never grows -> depth 0 -> nothing unlocks,
    even at the big cap (the load-bearing control: the climb is driven by real compositions, not the cap).

Outputs runs/r171_depth/{panel.png, world.gif}. panel = the embodied diet/capability ceiling + culture depth
trajectories measured from the LIVING population each step; world.gif = the uncapped world developing, agents
coloured violet->gold by realized culture depth (= what their bodies can do). Single foreground run, no
background tasks.
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

OUT = "runs/r171_depth"
_LOCKED = np.array([0.42, 0.13, 0.62])    # violet (shallow culture -> base body)
_UNLOCKED = np.array([1.0, 0.80, 0.10])   # gold   (deep culture -> full body)


def _cfg(K, innov_steps=3):
    return civ_config(
        tech_actions=False, tech_capabilities=False, generative_tree=True, depth_gates=True,
        max_techniques=K, innov_steps=innov_steps, n_food_tiers=5, recipe_level_step=2,
        n_capabilities=2, cap_level_step=2, tier0_frac=0.4,
        n0=300, capacity=1000, food_cap=600, food_regrow=40)


def _depth_color(world: GenesisWorld) -> np.ndarray:
    act = world.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    t = world.pop.tech[act]
    frac = (t / max(float(world.cfg.recipe_level_step * (world.cfg.n_food_tiers - 1)), 1.0))[:, None]
    frac = np.clip(frac, 0.0, 1.0)
    return _LOCKED * (1.0 - frac) + _UNLOCKED * frac


def run(world: GenesisWorld, steps: int, every: int = 10):
    S, DEPTH, TIER, AXES, POP = [], [], [], [], []
    for s in range(steps):
        world.step()
        if s % every:
            continue
        act = world.pop.active()
        tier, axes = world.diet_capability_ceiling()
        S.append(s)
        DEPTH.append(float(world.pop.tech[act].max()) if act.size else 0.0)
        TIER.append(tier)
        AXES.append(axes)
        POP.append(int(act.size))
    return dict(s=S, depth=DEPTH, tier=TIER, axes=AXES, pop=POP)


def render_gif(world: GenesisWorld, frames: int = 28):
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
    steps = 320
    t0 = time.time()
    print("[r171] uncapped (K=4000)...")
    big_world = GenesisWorld(_cfg(4000), seed=1)
    big = run(big_world, steps)
    print("[r171] capped (K=20)...")
    small = run(GenesisWorld(_cfg(20), seed=1), steps)
    print("[r171] null (K=4000, innov_steps=0)...")
    null = run(GenesisWorld(_cfg(4000, innov_steps=0), seed=1), steps)
    print(f"[r171] sims done in {time.time()-t0:.0f}s")
    print("[r171] rendering developed uncapped world...")
    nfr, last = render_gif(big_world, frames=28)

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    for d, c, lab in [(big, "#d4a017", "uncapped K=4000"), (small, "#c0392b", "capped K=20"),
                      (null, "tab:gray", "null innov=0")]:
        ax[0, 0].plot(d["s"], d["depth"], color=c, lw=2.0, label=lab)
        ax[0, 1].plot(d["s"], d["tier"], color=c, lw=2.0, label=lab)
        ax[1, 0].plot(d["s"], d["axes"], color=c, lw=2.0, label=lab)
    ax[0, 0].set_title("cultural DEPTH (deepest known level)")
    ax[0, 1].set_title("embodied DIET ceiling (deepest edible tier)")
    ax[0, 1].set_ylim(-0.3, (big["tier"][-1] + 0.5) if big["tier"] else 4.5)
    ax[1, 0].set_title("capability AXES unlocked (speed, reach)")
    ax[1, 0].set_ylim(-0.2, 2.3)
    for a in (ax[0, 0], ax[0, 1], ax[1, 0]):
        a.set_xlabel("step"); a.grid(alpha=0.3); a.legend(fontsize=8)
    if last is not None:
        ax[1, 1].imshow(last)
        ax[1, 1].set_title(f"developed uncapped world (violet->gold = culture depth = body), {nfr} frames")
    ax[1, 1].axis("off")
    fig.suptitle("R171 — open-ended culture CAUSALLY drives the body: embodied ceiling tracks the cultural cap",
                 fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(f"{OUT}/panel.png", dpi=110)
    print(f"[r171] wrote {OUT}/panel.png + world.gif ({nfr} frames)")

    print(f"[r171] HEADLINE uncapped: depth {big['depth'][0]:.0f}->{big['depth'][-1]:.0f}, "
          f"diet tier ->{big['tier'][-1]}, axes ->{big['axes'][-1]}, pop {big['pop'][-1]}")
    print(f"[r171] CAPPED:   depth ->{small['depth'][-1]:.0f}, diet tier ->{small['tier'][-1]}, "
          f"axes ->{small['axes'][-1]}, pop {small['pop'][-1]}")
    print(f"[r171] NULL:     depth ->{null['depth'][-1]:.0f}, diet tier ->{null['tier'][-1]}, "
          f"axes ->{null['axes'][-1]}, pop {null['pop'][-1]}")
    print(f"[r171] total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
