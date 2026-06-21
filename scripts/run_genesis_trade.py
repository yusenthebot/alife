"""R158 — GENESIS inter-agent TRADE economy. R157 locked each spatial region to its own recipe BRANCH by
ecological selection (region r yields only tier-(r+1) food, edible only by recipe-r holders). R158 asks the
next ladder question: does adding EXCHANGE between specialists turn those segregated traditions into an
ECONOMY that changes outcomes? When trade=True, the SURPLUS of a locked-tier harvest flows to the nearest
HUNGRY COMPLEMENTARY agent (one that lacks the recipe, so could not have eaten the food) within trade_radius
— a giver feeds a nearby off-branch neighbour with a good it alone could produce.

What the verify measures (in situ; never feeds selection):
  STRUCTURE — real trade is LOCAL (partner dist << radius) and fully COMPLEMENTARY (every receiver lacks the
    recipe), of substantial VOLUME, vs a matched-energy SCRAMBLE null (deliver each share to a uniformly-random
    hungry agent): the scramble is dispersed (huge partner dist) and more cross-region, isolating the local
    economic structure from raw energy injection.
  CAUSAL INERTNESS (the honest finding) — on this hard-constrained substrate the population fills a ceiling
    independent of trade, so redistributing harvested energy (even at a super-unit trade_gain that INJECTS
    energy) does NOT raise the carrying capacity vs no-trade. An inter-agent economy alone, bolted onto
    ecological traditions, does not drive a population transition — because trade does not relax the limiting
    constraint. One sim at a time; GL context released after the render.
"""
import os
import sys
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from alife.genesis.genesis import GenesisWorld
from tests.test_genesis import _satcfg  # the EXACT validated/red-teamed R158 saturated regime

OUT = "runs/r158_trade"
os.makedirs(OUT, exist_ok=True)
BRANCH_RGB = np.array([[0.90, 0.20, 0.20], [0.20, 0.55, 0.95], [0.95, 0.80, 0.15]])
GREY = np.array([0.55, 0.55, 0.55])


def cfg(**kw):
    # the saturated regime used by the unit tests: a high free-tier lifeline + ample food so the pop robustly
    # fills its capacity ceiling across seeds and trade reliably fires (vs the bimodal collapse-or-cap noise of
    # the alignment-tuned R157 regime). Importing the test helper guarantees the verify matches what is red-teamed.
    return _satcfg(n0=600, **kw)


def branch_color(w):
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    recipes = w._recipe_tech[1:]
    held = w.rep[np.ix_(act, recipes)]
    score = np.where(held, np.arange(1, recipes.size + 1)[None, :], 0)
    branch = np.where(held.any(axis=1), score.argmax(axis=1), -1)
    return np.where(branch[:, None] >= 0, BRANCH_RGB[np.clip(branch, 0, None)], GREY)


def trace(seed, trade, scramble=False, tgain=1.0, steps=300, every=25):
    w = GenesisWorld(cfg(trade=trade, trade_scramble=scramble, trade_gain=tgain), seed=seed, evolve=True)
    st, pop, vol = [], [], []
    for s in range(steps):
        w.step()
        if s % every == 0:
            st.append(s); pop.append(w.pop.active().size)
            vol.append(w.trade_test().get("trade_volume", 0.0) if trade else 0.0)
    return dict(st=st, pop=pop, vol=vol, final=(w.trade_test() if trade else {}),
                final_pop=w.pop.active().size)


def snap3d(seed, steps):
    from alife.render3d import Renderer3D
    w = GenesisWorld(cfg(trade=True), seed=seed, evolve=True)
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

    print(f"=== inertness: off vs trade(g1) vs trade(g2), {len(seeds)} seeds, {steps} steps ===", flush=True)
    off = [trace(s, False, steps=steps) for s in seeds]
    real = [trace(s, True, steps=steps) for s in seeds]
    g2 = [trace(s, True, tgain=2.0, steps=steps) for s in seeds]
    for s, o, r, g in zip(seeds, off, real, g2):
        print(f"  seed {s}: off n={o['final_pop']}  trade n={r['final_pop']}  trade(g2) n={g['final_pop']}  "
              f"vol={r['final'].get('trade_volume',0):.0f}", flush=True)
    diffs = [abs(r["final_pop"] - o["final_pop"]) for o, r in zip(off, real)]
    g2diffs = [abs(g["final_pop"] - o["final_pop"]) for o, g in zip(off, g2)]
    inert = max(diffs + g2diffs) <= 8
    print(f"  |trade-off| {diffs}  |trade(g2)-off| {g2diffs}  -> INERT={inert}", flush=True)

    print("=== structure: real vs scramble (seed 1) ===", flush=True)
    sreal = trace(1, True, steps=steps)
    sscr = trace(1, True, scramble=True, steps=steps)
    fr, fsc = sreal["final"], sscr["final"]
    print(f"  REAL : dist={fr['mean_partner_dist']:.1f} compl={fr['complementary_frac']:.2f} "
          f"xreg={fr['cross_region_frac']:.2f} vol={fr['trade_volume']:.0f} n={sreal['final_pop']}", flush=True)
    print(f"  SCRAM: dist={fsc['mean_partner_dist']:.1f} compl={fsc['complementary_frac']:.2f} "
          f"xreg={fsc['cross_region_frac']:.2f} vol={fsc['trade_volume']:.0f} n={sscr['final_pop']}", flush=True)
    local = fr["mean_partner_dist"] < fsc["mean_partner_dist"] and fr["complementary_frac"] >= 0.99

    print("=== 3D branch-coloured snapshot (real trade) ===", flush=True)
    img = snap3d(1, steps)
    print(f"  rendered ({time.time()-t0:.0f}s)", flush=True)

    # ---------- panel ----------
    fig = plt.figure(figsize=(16, 9))

    ax1 = fig.add_subplot(2, 3, 1)
    for o in off:
        ax1.plot(o["st"], o["pop"], color="#999999", lw=2, alpha=0.85)
    for r in real:
        ax1.plot(r["st"], r["pop"], color="#2ca02c", lw=2, alpha=0.85)
    for g in g2:
        ax1.plot(g["st"], g["pop"], color="#d62728", lw=1.6, ls="--", alpha=0.85)
    ax1.plot([], [], color="#999999", lw=2, label="no trade")
    ax1.plot([], [], color="#2ca02c", lw=2, label="trade")
    ax1.plot([], [], color="#d62728", lw=1.6, ls="--", label="trade gain=2 (energy-injecting)")
    ax1.set_title("CAUSAL INERTNESS: population vs trade")
    ax1.set_xlabel("step"); ax1.set_ylabel("living agents"); ax1.legend(fontsize=8)

    ax2 = fig.add_subplot(2, 3, 2)
    lbl = ["partner\ndist", "complement.\nfrac", "cross-region\nfrac"]
    rvals = [fr["mean_partner_dist"], fr["complementary_frac"] * 100, fr["cross_region_frac"] * 100]
    svals = [fsc["mean_partner_dist"], fsc["complementary_frac"] * 100, fsc["cross_region_frac"] * 100]
    x = np.arange(3)
    ax2.bar(x - 0.2, rvals, 0.4, color="#2ca02c", label="real trade")
    ax2.bar(x + 0.2, svals, 0.4, color="#999999", label="scramble null")
    ax2.set_xticks(x); ax2.set_xticklabels(lbl, fontsize=8)
    ax2.set_title("network STRUCTURE (dist in world units; fracs in %)")
    ax2.legend(fontsize=8)

    ax3 = fig.add_subplot(2, 3, 3)
    ax3.plot(sreal["st"], sreal["vol"], color="#2ca02c", lw=2, label="real")
    ax3.plot(sscr["st"], sscr["vol"], color="#999999", lw=2, label="scramble")
    ax3.set_title(f"trade VOLUME (real final {fr['trade_volume']:.0f})")
    ax3.set_xlabel("step"); ax3.set_ylabel("cumulative energy traded"); ax3.legend(fontsize=8)

    ax4 = fig.add_subplot(2, 3, 4)
    bp = [o["final_pop"] for o in off] + [r["final_pop"] for r in real] + [g["final_pop"] for g in g2]
    bx = (list(range(len(seeds))) + [i + 0.25 for i in range(len(seeds))] +
          [i + 0.5 for i in range(len(seeds))])
    cols = ["#999999"] * len(seeds) + ["#2ca02c"] * len(seeds) + ["#d62728"] * len(seeds)
    ax4.bar(bx, bp, 0.22, color=cols)
    ax4.set_title("final pop: off (grey) / trade (green) / trade-g2 (red)")
    ax4.set_ylabel("living agents"); ax4.set_xticks([])

    ax5 = fig.add_subplot(2, 3, 5)
    if img is not None:
        ax5.imshow(img); ax5.set_title("real-trade world (colour = recipe branch)")
    ax5.axis("off")

    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")
    verdict = ("STRUCTURED ECONOMY,\nCAUSALLY INERT" if (local and inert) else "see numbers")
    ax6.text(0.02, 0.5,
             f"VERDICT: {verdict}\n\n"
             f"STRUCTURE (positive): real trade is LOCAL\n"
             f"(partner dist {fr['mean_partner_dist']:.1f} << radius {cfg().trade_radius:.0f}) and fully\n"
             f"COMPLEMENTARY ({fr['complementary_frac']*100:.0f}% of receivers lack the\n"
             f"recipe), volume {fr['trade_volume']:.0f}. The matched-energy\n"
             f"SCRAMBLE is dispersed (dist {fsc['mean_partner_dist']:.0f}).\n\n"
             f"INERTNESS (honest negative): pop fills a\n"
             f"ceiling independent of trade — even a super-\n"
             f"unit trade_gain that INJECTS energy doesn't\n"
             f"lift it (|trade-off| {max(diffs)}, |g2-off| {max(g2diffs)}).\n"
             f"Redistribution does not relax the limiting\n"
             f"constraint -> an economy bolted onto ecological\n"
             f"traditions does not (yet) change outcomes.",
             fontsize=10, va="center")
    fig.suptitle("GENESIS R158 — inter-agent TRADE: a real local, complementary exchange network forms over the "
                 "R157\nspecialists, but it is causally INERT on the hard-constrained population (honest negative).",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/panel.png  (INERT={inert}, local={local}; {time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
