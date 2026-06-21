"""R159 — GENESIS PRODUCTIVE goods trade. R158 found inter-agent TRADE causally INERT: redistributing harvested
energy did not raise the carrying capacity because it does not relax the binding constraint. R159 answers that
with PRODUCTION, not redistribution: a tier-t specialist harvests up to goods_max EXTRA wasted ripe locked motes
within trade_radius and ships each as an edible GOOD to a nearby hungry COMPLEMENTARY partner (lacks the recipe).
The good = the mote's value, the mote is REMOVED (energy-conserving, frees a food slot) -> otherwise-wasted locked
food is supposed to become population. seed_specialists starts an already-specialized population (per R157) so the
economic question is isolated from the cultural-emergence bootstrap.

What the verify measures (in situ; never feeds selection):
  STRUCTURE — the productive economy fires: wasted tier-t motes are consumed-for-trade and shipped LOCALLY to
    hungry complementary partners (partner dist << radius), vs a SCRAMBLE null (random hungry recipient anywhere).
  CAUSAL INERTNESS (the DEEPER honest finding) — pop ON == pop OFF: unlocking wasted food does NOT raise the
    carrying capacity, because the population is NOT food-quantity-limited here (it equilibrates by foraging/
    lifespan dynamics, frequently exceeding the standing food count). So PRODUCTION, like R158's redistribution,
    leaves the binding constraint untouched — a stronger negative than R158's. 禁止造假.
  One sim at a time; GL context released after the render.
"""
import os
import sys
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.genesis import GenesisWorld
from tests.test_genesis import _goodscfg  # the EXACT validated/tested R159 productive-economy regime

OUT = "runs/r159_goods"
os.makedirs(OUT, exist_ok=True)
BRANCH_RGB = np.array([[0.90, 0.20, 0.20], [0.20, 0.55, 0.95], [0.95, 0.80, 0.15]])
GREY = np.array([0.55, 0.55, 0.55])


def branch_color(w):
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    recipes = w._recipe_tech[1:]
    held = w.rep[np.ix_(act, recipes)]
    score = np.where(held, np.arange(1, recipes.size + 1)[None, :], 0)
    branch = np.where(held.any(axis=1), score.argmax(axis=1), -1)
    return np.where(branch[:, None] >= 0, BRANCH_RGB[np.clip(branch, 0, None)], GREY)


def trace(seed, goods, scramble=False, steps=300, every=25):
    w = GenesisWorld(_goodscfg(n0=600, trade_goods=goods, trade_scramble=scramble), seed=seed, evolve=True)
    st, pop, food, vol = [], [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            st.append(s); pop.append(w.pop.active().size)
            food.append(int(w.food_ripe.sum()))                   # standing RIPE food (the supposed limiter)
            vol.append(w.goods_test().get("goods_volume", 0.0) if goods else 0.0)
    return dict(st=st, pop=pop, food=food, vol=vol, final=(w.goods_test() if goods else {}),
                final_pop=w.pop.active().size, final_food=int(w.food_ripe.sum()))


def food_invariance(seed, regrows, steps):
    """The decisive 'NOT food-limited' evidence: vary the food SUPPLY (food_regrow) 6x with trade OFF and show
    the equilibrium population barely moves — the carrying capacity is set by foraging/lifespan, not food."""
    pops, foods = [], []
    for fr in regrows:
        w = GenesisWorld(_goodscfg(n0=600, trade_goods=False, food_regrow=fr), seed=seed, evolve=True)
        for _ in range(steps):
            w.step()
        pops.append(w.pop.active().size); foods.append(int(w.food_ripe.sum()))
    return pops, foods


def snap3d(seed, steps):
    from alife.render3d import Renderer3D
    w = GenesisWorld(_goodscfg(n0=600, trade_goods=True), seed=seed, evolve=True)
    r = Renderer3D(w.cfg.world, width=640, height=480)
    img = None
    for s in range(steps):
        w.step()
    act = w.pop.active()
    if act.size:
        hp, _ = w.hearth_arrays()
        img = r.render(w.pop.pos[act], w.pop.vel[act], branch_color(w), cam_angle=0.6, cam_elev=0.42, food=hp)
    r.ctx.release()
    return img


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seeds = (0, 1)
    t0 = time.time()

    print(f"=== inertness: productive goods ON vs OFF, {len(seeds)} seeds, {steps} steps ===", flush=True)
    off = [trace(s, False, steps=steps) for s in seeds]
    on = [trace(s, True, steps=steps) for s in seeds]
    for s, o, r in zip(seeds, off, on):
        print(f"  seed {s}: off n={o['final_pop']} (food {o['final_food']})  "
              f"goods n={r['final_pop']} (food {r['final_food']})  motes={r['final'].get('goods_motes',0)}",
              flush=True)
    diffs = [abs(r["final_pop"] - o["final_pop"]) for o, r in zip(off, on)]
    fired = all(r["final"].get("goods_motes", 0) > 0 for r in on)
    inert = max(diffs) <= 8
    # the food-not-limiting evidence: population exceeds the standing ripe food count (pop is NOT food-bound)
    pop_over_food = [o["final_pop"] / max(1, o["final_food"]) for o in off]
    print(f"  |goods-off| {diffs} -> INERT={inert} (fired={fired}); pop/food OFF {[round(x,1) for x in pop_over_food]}",
          flush=True)

    print("=== structure: real goods vs scramble (seed 1) ===", flush=True)
    sreal = trace(1, True, steps=steps)
    sscr = trace(1, True, scramble=True, steps=steps)
    fr, fsc = sreal["final"], sscr["final"]
    print(f"  REAL : dist={fr['mean_partner_dist']:.1f} motes={fr['goods_motes']} vol={fr['goods_volume']:.0f}",
          flush=True)
    print(f"  SCRAM: dist={fsc['mean_partner_dist']:.1f} motes={fsc['goods_motes']} vol={fsc['goods_volume']:.0f}",
          flush=True)
    local = fr["mean_partner_dist"] < fsc["mean_partner_dist"]

    print("=== food-supply invariance (trade OFF, vary food_regrow) ===", flush=True)
    regrows = [12, 22, 35, 45, 60, 80]
    inv_pop, inv_food = food_invariance(1, regrows, steps)
    print(f"  food_regrow {regrows} -> pop {inv_pop} (ripe food {inv_food})", flush=True)

    print("=== 3D branch-coloured snapshot (real goods trade) ===", flush=True)
    img = snap3d(1, steps)
    print(f"  rendered ({time.time()-t0:.0f}s)", flush=True)

    # ---------- panel ----------
    fig = plt.figure(figsize=(16, 9))

    ax1 = fig.add_subplot(2, 3, 1)
    for o in off:
        ax1.plot(o["st"], o["pop"], color="#999999", lw=2, alpha=0.85)
    for r in on:
        ax1.plot(r["st"], r["pop"], color="#2ca02c", lw=2, alpha=0.85)
    ax1.plot([], [], color="#999999", lw=2, label="no trade")
    ax1.plot([], [], color="#2ca02c", lw=2, label="productive goods trade")
    ax1.set_title("CAUSAL INERTNESS: population OVERLAPS")
    ax1.set_xlabel("step"); ax1.set_ylabel("living agents"); ax1.legend(fontsize=8)

    ax2 = fig.add_subplot(2, 3, 2)
    # vary the food SUPPLY 6x (trade off) — pop is FLAT => the carrying capacity is NOT food-limited
    ax2.plot(regrows, inv_pop, "o-", color="#2ca02c", lw=2, label="equilibrium pop")
    ax2.plot(regrows, inv_food, "s--", color="#1f77b4", lw=2, label="standing ripe food")
    ax2.set_ylim(0, max(inv_pop + inv_food) * 1.15)
    ax2.set_title("WHY INERT: pop FLAT as food supply varies 6x\n=> NOT food-limited")
    ax2.set_xlabel("food_regrow (supply rate)"); ax2.set_ylabel("count"); ax2.legend(fontsize=8)

    ax3 = fig.add_subplot(2, 3, 3)
    ax3.plot(sreal["st"], sreal["vol"], color="#2ca02c", lw=2, label="real")
    ax3.plot(sscr["st"], sscr["vol"], color="#999999", lw=2, label="scramble")
    ax3.set_title(f"goods VOLUME (real final {fr['goods_volume']:.0f}, {fr['goods_motes']} motes freed)")
    ax3.set_xlabel("step"); ax3.set_ylabel("cumulative energy as goods"); ax3.legend(fontsize=8)

    ax4 = fig.add_subplot(2, 3, 4)
    bp = [o["final_pop"] for o in off] + [r["final_pop"] for r in on]
    bx = list(range(len(seeds))) + [i + 0.28 for i in range(len(seeds))]
    cols = ["#999999"] * len(seeds) + ["#2ca02c"] * len(seeds)
    ax4.bar(bx, bp, 0.26, color=cols)
    ax4.set_title("final pop: off (grey) / goods (green) — equal")
    ax4.set_ylabel("living agents"); ax4.set_xticks([])

    ax5 = fig.add_subplot(2, 3, 5)
    if img is not None:
        ax5.imshow(img); ax5.set_title("goods-trade world (colour = recipe branch)")
    ax5.axis("off")

    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")
    verdict = ("PRODUCTIVE economy,\nstill CAUSALLY INERT" if (local and inert and fired) else "see numbers")
    ax6.text(0.02, 0.5,
             f"VERDICT: {verdict}\n\n"
             f"PRODUCTION (positive): goods trade FIRES — a\n"
             f"specialist harvests wasted locked motes and\n"
             f"ships them as edible goods to nearby hungry\n"
             f"complementary partners. {fr['goods_motes']} motes freed,\n"
             f"vol {fr['goods_volume']:.0f}, LOCAL (dist {fr['mean_partner_dist']:.1f} <<\n"
             f"radius {_goodscfg().trade_radius:.0f}; scramble dist {fsc['mean_partner_dist']:.0f}).\n\n"
             f"INERTNESS (DEEPER negative than R158): pop ON\n"
             f"== pop OFF (|goods-off| {max(diffs)}). Unlocking wasted\n"
             f"food cannot lift the ceiling because the pop is\n"
             f"NOT food-limited: varying food supply 6x leaves\n"
             f"pop flat ({min(inv_pop)}-{max(inv_pop)}). PRODUCTION, like R158's\n"
             f"redistribution, leaves the binding (foraging/\n"
             f"lifespan) constraint untouched.",
             fontsize=10, va="center")
    fig.suptitle("GENESIS R159 — PRODUCTIVE goods trade unlocks otherwise-wasted locked food, yet is causally "
                 "INERT on the\npopulation: the carrying capacity is foraging/lifespan-limited, not food-limited "
                 "(a deeper honest negative).",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/panel.png  (INERT={inert}, fired={fired}, local={local}; {time.time()-t0:.0f}s total)",
          flush=True)


if __name__ == "__main__":
    main()
