"""R153 — GENESIS culture UNLOCKS world-actions. Until R153 the learned `tech` only multiplied a harvest
SCALAR (1+tech_gain*tech): cultural depth changed a NUMBER, not what an agent DID. R153 makes culture change
a PHYSICAL action. Food spawns in recipe-locked TIERS; a tier-t mote (t>=1) is edible ONLY by an agent whose
combinatorial repertoire holds that tier's RECIPE technique (a deep tech-tree node; tier t needs tree-level
>= recipe_level_step*t). So a deeper culture physically UNLOCKS richer food the world otherwise denies — the
realized DIET widens with cultural depth, and only TRANSMISSION (not one asocial lifetime from an empty
repertoire) reaches the deep recipes.

FALSIFIABLE claim + controls (in situ; never feed selection):
  (1) UNLOCKS — with social learning the population climbs to the deep recipe techniques and physically
      unlocks more food tiers (realized_tiers and mean_edible_tiers rise).
  (2) TRANSMISSION-REQUIRED (acid test) — the ASOCIAL control (learn=False) stays locked near tier 0; rich
      food rots uneaten (high locked_food_frac). Cumulative cultural capability is impossible in one lifetime.
  (3) IT MATTERS PHYSICALLY (load-bearing) — because unlocked tiers are a real resource, the social world
      sustains a far larger population than the asocial one; this is not a decorative scalar but exploited food.
  (4) DISTINCT FROM THE R150 SCALAR — tech_actions=False never changes the realized diet (byte-identical guard
      in tests); here the new axis is a PHYSICAL action gated by culture, not a payoff multiplier.
One sim at a time; GL context released after the render. 禁止造假 — every number is read from the live world.
"""
import os
import sys
import time
from dataclasses import replace

import imageio.v2 as imageio
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.genesis import GenesisConfig, GenesisWorld
from alife.world3d import World3D

OUT = "runs/r153_recipes"
os.makedirs(OUT, exist_ok=True)
LOCKED = np.array([0.95, 0.30, 0.12])    # red-orange = tier-0-only (culturally locked out)
UNLOCKED = np.array([0.25, 1.0, 0.45])   # bright green = full realized diet (deep culture)


def cfg(**kw):
    # the viable building+combinatorial-culture regime; tier-0 (the free resource) sustains a modest population
    # even asocially, so the locked tiers are a real cultural BONUS the world stays alive to exploit (or not).
    base = dict(processing=True, building=True, culture=True, combinatorial=True, max_techniques=2000,
                n_seed_tech=6, innov_steps=1, hearth_reach_per_strength=3.0, hearth_radius=12.0,
                tech_actions=True, n_food_tiers=4, recipe_level_step=1, tier_value_bonus=2.0, tier0_frac=0.7,
                food_cap=1200, food_regrow=70, capacity=2000)
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=600), **base)


def agent_color(w):
    """Colour each agent by its REALIZED DIET BREADTH — how many food tiers its culture has unlocked."""
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    recipes = w._recipe_tech[1:]
    breadth = 1 + w.rep[np.ix_(act, recipes)].sum(axis=1)             # 1..n_food_tiers
    frac = ((breadth - 1) / max(w.cfg.n_food_tiers - 1, 1))[:, None]  # 0=locked, 1=full diet
    return LOCKED * (1.0 - frac) + UNLOCKED * frac


def trace(steps, seed, learn=True, every=40, render=False, render_every=120):
    w = GenesisWorld(cfg(learn=learn), seed=seed, evolve=True)
    st, rt, met, lf, pop = [], [], [], [], []
    frames = []
    r = None
    if render:
        from alife.render3d import Renderer3D
        r = Renderer3D(w.cfg.world, width=720, height=540)
    for s in range(steps):
        w.step()
        if s % every == 0:
            ta = w.tech_actions_test()
            st.append(s); rt.append(ta.get("realized_tiers", 0)); met.append(ta.get("mean_edible_tiers", 0.0))
            lf.append(ta.get("locked_food_frac", 0.0)); pop.append(ta.get("n", 0))
        if render and s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], agent_color(w),
                                       cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    ta = w.tech_actions_test()
    out = dict(st=st, rt=rt, met=met, lf=lf, pop=pop, final=ta, tier_eats=ta.get("tier_eats", []))
    if render:
        r.ctx.release()
        if frames:
            imageio.mimsave(os.path.join(OUT, "recipes.gif"), frames, fps=8, loop=0)
        out["frames"] = len(frames)
    return out


def mean_trace(runs, key):
    n = min(len(r[key]) for r in runs)
    return np.mean([r[key][:n] for r in runs], axis=0), runs[0]["st"][:n]


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 900
    cs = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    seeds = (0, 1)
    t0 = time.time()
    print(f"=== headline social run ({steps} steps, diet-breadth-coloured 3D) ===", flush=True)
    h = trace(steps, seed=0, learn=True, render=True)
    hf = h["final"]
    print(f"headline: pop {hf['n']} realized_tiers {hf['realized_tiers']}/{hf['max_tiers']} "
          f"mean_edible {hf['mean_edible_tiers']:.2f} locked_food_frac {hf['locked_food_frac']:.2f} "
          f"({h.get('frames',0)} frames, {time.time()-t0:.0f}s)", flush=True)

    print(f"=== controls: social vs asocial, {len(seeds)} seeds, {cs} steps ===", flush=True)
    soc = [trace(cs, s, learn=True) for s in seeds]
    aso = [trace(cs, s, learn=False) for s in seeds]
    for s, rs, ra in zip(seeds, soc, aso):
        fs, fa = rs["final"], ra["final"]
        print(f"  seed {s}: SOCIAL tiers {fs['realized_tiers']}/{fs['max_tiers']} edible {fs['mean_edible_tiers']:.2f} "
              f"pop {fs['n']} locked {fs['locked_food_frac']:.2f} | ASOCIAL tiers {fa['realized_tiers']} "
              f"edible {fa['mean_edible_tiers']:.2f} pop {fa['n']} locked {fa['locked_food_frac']:.2f}", flush=True)

    soc_rt = np.mean([r["final"]["realized_tiers"] for r in soc])
    aso_rt = np.mean([r["final"]["realized_tiers"] for r in aso])
    soc_ed = np.mean([r["final"]["mean_edible_tiers"] for r in soc])
    aso_ed = np.mean([r["final"]["mean_edible_tiers"] for r in aso])
    soc_pop = np.mean([r["final"]["n"] for r in soc])
    aso_pop = np.mean([r["final"]["n"] for r in aso])
    soc_lf = np.mean([r["final"]["locked_food_frac"] for r in soc])
    aso_lf = np.mean([r["final"]["locked_food_frac"] for r in aso])
    print(f"  MEAN realized_tiers: social {soc_rt:.2f} vs asocial {aso_rt:.2f} (max {soc[0]['final']['max_tiers']})",
          flush=True)
    print(f"  MEAN mean_edible_tiers: social {soc_ed:.2f} vs asocial {aso_ed:.2f}", flush=True)
    print(f"  MEAN population: social {soc_pop:.0f} vs asocial {aso_pop:.0f} ({soc_pop/max(aso_pop,1):.1f}x)",
          flush=True)
    print(f"  MEAN locked_food_frac: social {soc_lf:.2f} vs asocial {aso_lf:.2f} "
          f"(rich food rots uneaten without the recipes)", flush=True)

    unlocks_more = soc_rt > aso_rt + 0.5                          # transmission unlocks strictly more tiers
    wider_diet = soc_ed > aso_ed + 0.5                            # the average agent physically eats wider
    transmission_required = aso_rt <= 2.0 and aso_lf > 0.4        # asocial stays locked, rich food rots
    load_bearing = soc_pop > 3 * aso_pop                          # unlocked tiers are exploited food, not decoration
    verdict = unlocks_more and wider_diet and transmission_required and load_bearing
    print(f"  CHECKS: unlocks-more {unlocks_more} | wider-diet {wider_diet} | "
          f"transmission-required {transmission_required} | load-bearing {load_bearing}", flush=True)
    print(f"  VERDICT: {'CULTURE UNLOCKS WORLD-ACTIONS' if verdict else 'NEGATIVE'}", flush=True)

    # ---- panel ----
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    s_rt, st = mean_trace(soc, "rt"); a_rt, _ = mean_trace(aso, "rt")
    ax[0, 0].plot(st, s_rt, color="#2ca02c", lw=2, label="social")
    ax[0, 0].plot(st, a_rt, color="#999999", lw=2, label="asocial")
    ax[0, 0].set_title(f"REALIZED TIERS unlocked: social {soc_rt:.1f} vs asocial {aso_rt:.1f} (max {soc[0]['final']['max_tiers']})")
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("food tiers the population can eat"); ax[0, 0].legend()
    s_ed, _ = mean_trace(soc, "met"); a_ed, _ = mean_trace(aso, "met")
    ax[0, 1].plot(st, s_ed, color="#2ca02c", lw=2, label="social")
    ax[0, 1].plot(st, a_ed, color="#999999", lw=2, label="asocial")
    ax[0, 1].set_title(f"DIET BREADTH per agent: social {soc_ed:.2f} vs asocial {aso_ed:.2f}")
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylabel("mean edible tiers / agent"); ax[0, 1].legend()
    s_lf, _ = mean_trace(soc, "lf"); a_lf, _ = mean_trace(aso, "lf")
    ax[0, 2].plot(st, s_lf, color="#2ca02c", lw=2, label="social")
    ax[0, 2].plot(st, a_lf, color="#999999", lw=2, label="asocial")
    ax[0, 2].set_title(f"LOCKED FOOD wasted: social {soc_lf:.2f} vs asocial {aso_lf:.2f}\n(fraction of ripe food no one can eat)")
    ax[0, 2].set_xlabel("step"); ax[0, 2].set_ylabel("locked_food_frac"); ax[0, 2].legend()
    s_pop, _ = mean_trace(soc, "pop"); a_pop, _ = mean_trace(aso, "pop")
    ax[1, 0].plot(st, s_pop, color="#2ca02c", lw=2, label="social")
    ax[1, 0].plot(st, a_pop, color="#999999", lw=2, label="asocial")
    ax[1, 0].set_title(f"POPULATION (load-bearing): social {soc_pop:.0f} vs asocial {aso_pop:.0f} ({soc_pop/max(aso_pop,1):.0f}x)")
    ax[1, 0].set_xlabel("step"); ax[1, 0].set_ylabel("living agents"); ax[1, 0].legend()
    # per-tier harvested-mote counts (cumulative) social vs asocial
    se = np.mean([r["final"].get("tier_eats", [0]) for r in soc], axis=0)
    ae = np.mean([r["final"].get("tier_eats", [0]) for r in aso], axis=0)
    x = np.arange(len(se))
    ax[1, 1].bar(x - 0.2, se, 0.4, color="#2ca02c", label="social")
    ax[1, 1].bar(x + 0.2, ae, 0.4, color="#999999", label="asocial")
    ax[1, 1].set_title("HARVESTED MOTES per tier (cumulative): social eats the locked tiers, asocial cannot")
    ax[1, 1].set_xlabel("food tier (0=free, 1+=recipe-locked)"); ax[1, 1].set_ylabel("motes eaten"); ax[1, 1].legend()
    ax[1, 2].axis("off")
    vtxt = "CULTURE UNLOCKS WORLD-ACTIONS" if verdict else "HONEST NEGATIVE"
    ax[1, 2].text(0.02, 0.95,
                  f"VERDICT: {vtxt}\n\n"
                  f"unlocks-more: {unlocks_more}\nwider-diet: {wider_diet}\n"
                  f"transmission-required: {transmission_required}\nload-bearing: {load_bearing}\n\n"
                  f"recipe techniques (tier->node):\n  {dict(enumerate(GenesisWorld(cfg(), seed=0)._recipe_tech.tolist()))}\n\n"
                  f"Mechanism: a tier-t food mote is edible ONLY by an agent whose\n"
                  f"learned repertoire holds that tier's recipe technique (a deep\n"
                  f"tech-tree node). Deeper CULTURE physically unlocks richer food —\n"
                  f"a real action, not a payoff scalar. Only TRANSMISSION reaches the\n"
                  f"deep recipes; the asocial world stays locked to the free tier.",
                  fontsize=10, va="top", family="monospace")
    fig.suptitle(f"GENESIS R153 — culture UNLOCKS world-actions: techniques gate what an agent can physically EAT.  {vtxt}\n"
                 f"(in recipes.gif: red=tier-0-only/locked, bright green=full realized diet; the social world "
                 f"brightens as recipes spread)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/recipes.gif and {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
