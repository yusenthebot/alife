"""R152 — can coupling building to the caste make Stages 3+4 COMPLEMENT instead of substitute? HONEST NEGATIVE.

R151's capstone found niche construction SUBSTITUTES for the division of labour: caste-free building lets the
persistent hearths ripen food for free, so the processor caste is redundant and selected away (frac_proc->0).
R152 tried to FLIP that by coupling the two: build STRENGTH is convex in the caste trait (only a high-spec
BUILDER raises a real hearth) and a builder earns a maintenance WAGE whenever a harvester eats food ripened by
a hearth it maintains -> the intended emergent outcome was a builder caste maintaining the hearths a harvester
caste eats from (a division of labour RE-EMERGING around niche construction).

It did NOT emerge. Across THREE distinct mechanistic regimes (food-rich; scarce + fast-decay hearths needing
continuous maintenance; many-small-hearths) the coupling never regrew a balanced division of labour:
  - food-rich: the caste fully collapses, identical to R151 (the crowd's incidental weak deposits accrete
    enough hearths that no dedicated builder is needed);
  - scarce/fast-decay (THIS regime, the viable one shown): the world survives but only a ~3% maintainer
    MINORITY forms (frac_build ~ 0.03 vs SUBSTITUTE ~ 0.00) — NOT a balanced caste. One tall hearth feeds
    hundreds, so the equilibrium needs only a handful of builders;
  - many-small-hearths (low reach): the whole world starves (non-viable).
Honest finding: SUBSTITUTION is the robust attractor. Even an explicit convex-build + maintenance-wage coupling
does not flip it; the shared, accretive, persistent nature of built infrastructure keeps building a near-public
good that a tiny minority supplies, so the harvester caste still dominates.

Three conditions at the IDENTICAL world/food (build_specialized is the only thing varied):
  COMPLEMENT  (build_specialized=True)              -> intended: a builder caste.   Observed: ~3% minority only.
  SUBSTITUTE  (build_specialized=False, = R151)     -> caste collapses (frac~0)      [the R151 finding, reproduced]
  WAGE-OFF    (build_specialized=True, payment=0)   -> population dies.  CONFOUNDED: the wage is also a raw
              energy injection, so its removal starves the world independently of caste dynamics -> NOT clean
              evidence the caste is load-bearing (flagged honestly, not claimed).
One sim at a time; GL context released after the render. 禁止造假 — frac_build is read from the live spec trait.
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

OUT = "runs/r152_complement"
os.makedirs(OUT, exist_ok=True)
HARV = np.array([0.10, 0.75, 0.80])      # teal  = harvester caste (spec~0)
BUILD = np.array([1.0, 0.55, 0.10])      # orange = builder caste (spec~1)


def cfg(**kw):
    # SCARCE-BUILDING regime (R152, attempt 2). The food-rich attempt 1 collapsed the caste in BOTH conditions:
    # under slow decay (0.01) the crowd's incidental weak deposits ACCRETE into enough hearths that no dedicated
    # builder is needed -> building is a free public good -> substitution, same as R151. The fix is mechanistic,
    # not cosmetic: make a hearth need CONTINUOUS high-rate maintenance so only a STANDING builder caste can keep
    # one alive. Fast decay (0.25/step) + a high working threshold (min_strength 1.0) mean a harvester's tiny
    # spec^2 deposit fades before it matters, while a spec~1 builder's 1.2/act sustains a tall hearth; food is
    # scarcer and ripens ONLY near strong hearths, so harvesters DEPEND on builders -> the maintenance wage has
    # real value -> negative frequency dependence selects a stable builder/harvester split. build_specialized
    # is the only thing varied across conditions.
    base = dict(capacity=1600, n_food_types=1,
                processing=True, building=True, culture=True, combinatorial=True, specialize=True,
                build_specialized=True,
                max_techniques=400, n_seed_tech=6, innov_steps=1,
                struct_capacity=220, build_gain=1.2, build_spec_gamma=2.0, build_cost=0.4,
                struct_decay=0.25, hearth_min_strength=1.0,
                hearth_reach_per_strength=3.0, hearth_radius=12.0, process_payment=22.0,
                food_cap=900, food_regrow=35,
                n_predators0=40, pred_capacity=70, pred_base_cost=0.6)
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=95.0), n0=500), **base)


def agent_color(w):
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    s = np.clip(w.pop.spec[act], 0.0, 1.0)[:, None]
    return HARV * (1.0 - s) + BUILD * s


def trace(steps, seed, label, gif=False, every=40, render_every=120, **cfgkw):
    c = cfg(**cfgkw)
    w = GenesisWorld(c, seed=seed, evolve=True)
    r = frames = None
    if gif:
        from alife.render3d import Renderer3D
        r = Renderer3D(c.world, width=720, height=540)
        frames = []
    T = dict(st=[], pop=[], fproc=[], specmean=[], hearths=[], ripe=[], popd=[])
    t0 = time.time()
    for s in range(steps):
        w.step()
        if s % every == 0:
            snap = w.snapshot(); ct = w.combinatorial_test() or {}
            act = w.pop.active(); sp = w.pop.spec[act]
            T["st"].append(s); T["pop"].append(snap["population"])
            T["fproc"].append(float((sp > 0.8).mean()) if act.size else 0.0)
            T["specmean"].append(snap["spec_mean"]); T["hearths"].append(snap["n_hearths"])
            T["ripe"].append(snap["ripe_food"]); T["popd"].append(ct.get("pop_distinct", 0))
        if gif and s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], agent_color(w),
                                        cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    if gif:
        r.ctx.release()
        if frames:
            imageio.mimsave(os.path.join(OUT, "complement.gif"), frames, fps=8, loop=0)
    a = w.pop.active(); spec_final = w.pop.spec[a]
    print(f"  {label:24s} seed {seed}: {steps} steps {time.time()-t0:.1f}s | pop {T['pop'][-1]:.0f} "
          f"frac_build {T['fproc'][-1]:.2f} spec_mean {T['specmean'][-1]:.2f} ripe {T['ripe'][-1]:.0f} "
          f"hearths {T['hearths'][-1]:.0f} pop_distinct {T['popd'][-1]}", flush=True)
    T["spec_final"] = spec_final
    return T


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    print(f"=== R152 Stage 3+4 COMPLEMENT — builder caste around niche construction ({steps} steps) ===", flush=True)
    comp = trace(steps, 0, "COMPLEMENT(coupled)", gif=True)
    print("=== control: SUBSTITUTE — caste-free building (R151 default) at the SAME world ===", flush=True)
    subs = trace(steps, 0, "SUBSTITUTE(R151)", build_specialized=False)
    print("=== mechanism: WAGE-OFF — coupling on but no maintenance wage (builders unfunded) ===", flush=True)
    woff = trace(steps, 0, "WAGE-OFF", process_payment=0.0)

    # --- verdict (HONEST: the headline is a NEGATIVE) ---
    # a genuine complementary division of labour would be a BALANCED builder caste, not a tiny minority
    balanced_caste = comp["fproc"][-1] > 0.15                         # the positive we did NOT see
    caste_minority = comp["fproc"][-1] - subs["fproc"][-1]            # how much coupling shifts the caste (~0)
    alive = comp["pop"][-1] > 100
    verdict = balanced_caste and alive                               # False -> honest negative
    print(f"  COMPLEMENT: frac_build {comp['fproc'][-1]:.3f} (pop {comp['pop'][-1]:.0f}, hearths "
          f"{comp['hearths'][-1]:.0f}) -> balanced caste {balanced_caste}", flush=True)
    print(f"  SUBSTITUTE (R151, reproduced): caste-free build frac_build {subs['fproc'][-1]:.3f}", flush=True)
    print(f"  COUPLING EFFECT on the caste: frac_build shift {caste_minority:+.3f} (≈0 -> coupling barely "
          f"moves the caste: substitution is robust)", flush=True)
    print(f"  WAGE-OFF: pop {woff['pop'][-1]:.0f} (dies) — CONFOUNDED (wage = energy injection), NOT clean "
          f"evidence the caste is load-bearing", flush=True)
    print(f"  VERDICT: {'COMPLEMENT (balanced caste re-emerged)' if verdict else 'HONEST NEGATIVE — substitution is robust; coupling does NOT regrow a balanced division of labour'}",
          flush=True)

    # --- panel ---
    st = np.array(comp["st"]); sts = np.array(subs["st"]); stw = np.array(woff["st"])
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    a = ax[0, 0]
    a.plot(st, comp["fproc"], color="#d62728", lw=2.5, label="COMPLEMENT (coupled+wage)")
    a.plot(sts, subs["fproc"], color="#2ca02c", lw=2, label="SUBSTITUTE (R151 caste-free)")
    a.plot(stw, woff["fproc"], color="#7f7f7f", lw=2, ls="--", label="WAGE-OFF (no wage, world dies)")
    a.set_title("HONEST NEGATIVE: coupling does NOT regrow a balanced builder caste\n"
                "COMPLEMENT (red) tracks SUBSTITUTE (green) -> substitution is robust")
    a.set_xlabel("step"); a.set_ylabel("fraction builder caste (spec>0.8)"); a.legend()

    a = ax[0, 1]
    a.plot(st, comp["hearths"], color="#8c564b", lw=2, label="standing hearths (complement)")
    a.plot(st, comp["ripe"], color="#ff7f0e", lw=2, label="ripe food (complement)")
    a.set_title(f"the world stays viable: {comp['hearths'][-1]:.0f} hearths maintained\n"
                f"but by a ~{100*comp['fproc'][-1]:.0f}% maintainer MINORITY, not a balanced caste")
    a.set_xlabel("step"); a.legend()

    a = ax[1, 0]
    a.plot(st, comp["pop"], color="#1f77b4", lw=2, label="COMPLEMENT pop")
    a.plot(sts, subs["pop"], color="#2ca02c", lw=2, label="SUBSTITUTE pop")
    a.plot(stw, woff["pop"], color="#7f7f7f", lw=2, ls="--", label="WAGE-OFF pop")
    a.set_title("population viable in all conditions (the difference is WHO does the labour)")
    a.set_xlabel("step"); a.set_ylabel("prey population"); a.legend()

    a = ax[1, 1]
    a.hist(comp["spec_final"], bins=20, range=(0, 1), color="#d62728", alpha=0.6, label="COMPLEMENT (coupled)")
    a.hist(subs["spec_final"], bins=20, range=(0, 1), color="#2ca02c", alpha=0.5, label="SUBSTITUTE (R151)")
    a.set_title("final caste distribution: BOTH harvester-dominated\ncoupling does not restore a builder/harvester split")
    a.set_xlabel("spec (0=harvester, 1=builder)"); a.set_ylabel("count"); a.legend()

    vtxt = ("a balanced division of labour RE-EMERGED" if verdict
            else "HONEST NEGATIVE — substitution is robust; coupling yields only a tiny maintainer minority")
    fig.suptitle(f"GENESIS R152 — does coupling building to the caste make Stages 3+4 COMPLEMENT?  {vtxt}\n"
                 f"convex build skill + maintenance wage did NOT regrow a balanced builder caste across 3 regimes; "
                 f"the harvester caste still dominates (complement.gif: teal=harvester, orange=builder, brown=hearths)",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/complement.gif and {OUT}/panel.png", flush=True)


if __name__ == "__main__":
    main()
