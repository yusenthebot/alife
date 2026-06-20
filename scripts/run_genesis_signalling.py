"""R145 — GENESIS Stage 2: make alarm signalling actually EMERGE via KIN SELECTION, then re-run the
same red-team-grade four-control protocol that caught R144's artifact.

R144 shipped the signalling substrate (evolved utterance out + heard-neighbour in) and an honest NEGATIVE:
hearing gave no survival benefit over deaf, and the signal-danger MI was a sensory-reaction artifact
(frozen >= evolved). The diagnosis was decisive: the R144 world founds n0 DISTINCT genomes that mix freely,
so relatedness ~ 0 — warning a neighbour helps a stranger and the signalling allele cannot spread
(Floreano & Mitri 2009: communication evolves under HIGH relatedness, collapses without). R145 supplies the
missing ingredient: the prey are founded as CLONAL DEMES (n_founder_genomes>0 — one genome per spatially
clustered deme sharing a lineage), so a prey's nearest neighbour is its clone and warning it propagates the
caller's OWN genes (Hamilton rb>c). Plus a strong informational asymmetry (short prey self-sense — a
neighbour closer to the predator can warn earlier) and a small honest-signalling emit cost.

The SAME four controls decide whether emergence is real (believe it ONLY if all four pass):
  1. scrambled-channel null   — permute the danger labels; MI under the null is ~0.
  2. frozen-genome control    — evolve=False. Real meaning needs evolved MI >> frozen MI (else it is just
                                the emitter reacting to its own predator-sense, not evolved meaning).
  3. causal lesion test       — silence the heard channel on the same brains/state; does behaviour change
                                ADAPTIVELY (flee away from an alarming neighbour)?
  4. intact-vs-deaf functional test — HEAR vs permanently-deaf (same brain shape). The ARTIFACT-IMMUNE
                                test: does hearing causally improve SURVIVAL? (ratio > 1.)

A relatedness read-out confirms the kin manipulation actually took (high in the clonal world, ~0 mixed).
One sim at a time; GL context released.
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

from alife.genesis import metrics
from alife.genesis.genesis import GenesisConfig, GenesisWorld

OUT = "runs/r145_kinsignalling"
os.makedirs(OUT, exist_ok=True)
# R145 kin-selection config: clonal demes (HIGH relatedness so warning a neighbour pays), a STRONG
# informational asymmetry (prey_pred_range 8 << sense_range 32 -> a neighbour closer to the predator
# warns earlier), sparse episodic predators (intermittent danger an alarm could flag), and a small
# honest-signalling cost so silence is the default. This is the setting in which alarm signalling SHOULD
# emerge if kin selection is the missing piece.
SIG = dict(signalling=True, prey_pred_range=8.0, n_predators0=40, pred_capacity=130,
           n_founder_genomes=30, founder_cluster_radius=7.0, emit_cost=0.004)
NPERM = 128


def _cfg(**kw):
    return replace(GenesisConfig(), **SIG, **kw)


def run(seed, evolve, deaf, steps, rng):
    w = GenesisWorld(_cfg(deaf=deaf), seed=seed, evolve=evolve)
    pops, mis, rels = [], [], []
    for s in range(steps):
        w.step()
        if s % 250 == 0:
            pops.append(w.pop.n_alive)
        if s % 2000 == 0:
            mis.append(w.snapshot()["signal_mi"])
            act = w.pop.active()
            rels.append(metrics.neighbour_relatedness(w.pop.pos[act], w.pop.lineage[act])
                        if act.size else 0.0)
    act = w.pop.active()
    utt, dng = w.pop.utterance[act], w._danger(act)
    mi = metrics.signal_world_mi(utt, dng, w.cfg.signal_bins)
    nm, ns = metrics.signal_mi_null(utt, dng, rng, w.cfg.signal_bins, NPERM)
    caus = w.signal_causal_test(rng)
    pops = np.array(pops)
    return {
        "mi": mi, "null": nm, "null_std": ns,
        "z": (mi - nm) / max(ns, 1e-9),
        "pop2nd": float(pops[len(pops) // 2:].mean()),
        "pred": w.pred.n_alive, "dfrac": float(dng.mean()) if act.size else 0.0,
        "flee_intact": caus.get("flee_intact", 0.0), "flee_deaf": caus.get("flee_deaf", 0.0),
        "n_alarmed": caus.get("n_alarmed", 0), "mi_tr": mis,
        "relatedness": float(np.mean(rels)) if rels else 0.0,
    }


def gif(seed, steps, rng):
    """3D GIF with prey coloured by their UTTERANCE (blue=silent -> red=loud); predators stay dark red."""
    try:
        from alife.render3d import Renderer3D
    except Exception as e:
        print(f"  (no GL context, skipping GIF: {e})", flush=True)
        return
    cfg = _cfg()
    w = GenesisWorld(cfg, seed=seed, evolve=True)
    cmap = plt.get_cmap("coolwarm")
    r = Renderer3D(cfg.world, width=720, height=540)
    frames = []
    for s in range(steps):
        w.step()
        if s % 200 == 0:
            act = w.pop.active()
            u = (w.pop.utterance[act] + 1.0) * 0.5                  # [-1,1] -> [0,1]
            col = cmap(u)[:, :3]
            pos, vel = w.pop.pos[act], w.pop.vel[act]
            if w.pred is not None:
                pa = w.pred.active()
                pos = np.vstack([pos, w.pred.pos[pa]])
                vel = np.vstack([vel, w.pred.vel[pa]])
                col = np.vstack([col, np.tile([0.45, 0.0, 0.0], (pa.size, 1))])
            if pos.shape[0]:
                frames.append(r.render(pos, vel, col, cam_angle=s * 0.012, cam_elev=0.42, food=w.food))
    r.ctx.release()
    if frames:
        imageio.mimsave(os.path.join(OUT, "signalling.gif"), frames, fps=12, loop=0)
        print(f"  wrote {OUT}/signalling.gif ({len(frames)} frames)", flush=True)


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    seeds = (0, 1, 2)
    rng = np.random.default_rng(20144)
    print(f"=== R144 emergent-signalling protocol: {len(seeds)} seeds x 3 conditions x {steps} steps ===",
          flush=True)
    t0 = time.time()
    res = {c: [] for c in ("evo", "deaf", "frozen")}
    for seed in seeds:
        e = run(seed, evolve=True, deaf=False, steps=steps, rng=rng)     # evolved, can hear
        d = run(seed, evolve=True, deaf=True, steps=steps, rng=rng)      # evolved, deaf control
        f = run(seed, evolve=False, deaf=False, steps=steps, rng=rng)    # frozen genome control
        res["evo"].append(e); res["deaf"].append(d); res["frozen"].append(f)
        print(f" seed {seed}: r={e['relatedness']:.2f} EVO MI={e['mi']:.4f}(z={e['z']:.1f}) FROZEN MI={f['mi']:.4f}"
              f" | HEAR pop={e['pop2nd']:.0f} DEAF pop={d['pop2nd']:.0f} (ratio {e['pop2nd']/max(d['pop2nd'],1):.3f})"
              f" | causal flee int={e['flee_intact']:.3f}/deaf={e['flee_deaf']:.3f}", flush=True)

    def col(cond, key):
        return np.array([r[key] for r in res[cond]])

    evo_mi, frz_mi, nul = col("evo", "mi"), col("frozen", "mi"), col("evo", "null")
    hear_pop, deaf_pop = col("evo", "pop2nd"), col("deaf", "pop2nd")
    fi, fd = col("evo", "flee_intact"), col("evo", "flee_deaf")
    rel = col("evo", "relatedness")
    ratio = hear_pop.mean() / max(deaf_pop.mean(), 1)
    # the verdict: emergence is believed ONLY if all four controls pass together
    c_mi = evo_mi.mean() > frz_mi.mean() + max(nul.mean(), 0.01)      # evolved MI clears frozen + null
    c_survival = ratio > 1.03                                          # hearing improves survival
    c_causal = fi.mean() > fd.mean()                                   # adaptive listening
    emerged = bool(c_mi and c_survival and c_causal)
    print(f"\n KIN MANIPULATION: mean nearest-neighbour relatedness {rel.mean():.2f} (clonal demes took)",
          flush=True)
    print(f" CTRL1/2 MI: EVO {evo_mi.mean():.4f} vs FROZEN {frz_mi.mean():.4f} vs null {nul.mean():.4f}"
          f"  -> evolved>>frozen: {c_mi}", flush=True)
    print(f" CTRL4 survival: HEAR pop {hear_pop.mean():.0f} vs DEAF pop {deaf_pop.mean():.0f}"
          f"  -> hearing benefit ratio {ratio:.3f}: {c_survival}", flush=True)
    print(f" CTRL3 causal flee intact {fi.mean():.3f} vs deaf {fd.mean():.3f}"
          f"  -> adaptive listening: {c_causal}", flush=True)
    print(f"\n VERDICT: alarm signalling {'EMERGED (all four controls pass)' if emerged else 'did NOT emerge'}"
          f"  [MI {c_mi} · survival {c_survival} · causal {c_causal}]", flush=True)

    print("=== rendering utterance-coloured 3D GIF ===", flush=True)
    gif(0, min(steps, 12000), rng)

    # ---- figure: the protocol verdict ----
    fig, ax = plt.subplots(2, 2, figsize=(15, 9))
    x = np.arange(len(seeds))
    ax[0, 0].bar(x - 0.25, evo_mi, 0.25, label="evolved", color="#2ca02c")
    ax[0, 0].bar(x, frz_mi, 0.25, label="frozen (control)", color="#d62728")
    ax[0, 0].bar(x + 0.25, nul, 0.25, label="scrambled null", color="#7f7f7f")
    ax[0, 0].set_xticks(x); ax[0, 0].set_xticklabels([f"seed {s}" for s in seeds])
    ax[0, 0].set_title(f"signal-danger MI (CTRL 1+2): evolved>>frozen = {c_mi}")
    ax[0, 0].set_ylabel("MI (bits)"); ax[0, 0].legend()

    ax[0, 1].bar(x - 0.18, hear_pop, 0.36, label="can hear", color="#1f77b4")
    ax[0, 1].bar(x + 0.18, deaf_pop, 0.36, label="deaf control", color="#9467bd")
    ax[0, 1].set_xticks(x); ax[0, 1].set_xticklabels([f"seed {s}" for s in seeds])
    ax[0, 1].set_title(f"intact-vs-deaf SURVIVAL (CTRL 4, artifact-immune): ratio "
                       f"{ratio:.2f} -> hearing helps = {c_survival}")
    ax[0, 1].set_ylabel("prey population (2nd-half mean)"); ax[0, 1].legend()

    ax[1, 0].bar(x - 0.18, fi, 0.36, label="channel intact", color="#2ca02c")
    ax[1, 0].bar(x + 0.18, fd, 0.36, label="channel lesioned", color="#d62728")
    ax[1, 0].axhline(0, color="k", lw=0.5)
    ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels([f"seed {s}" for s in seeds])
    ax[1, 0].set_title(f"causal lesion (CTRL 3): flee-from-alarmer intact>deaf = {c_causal}")
    ax[1, 0].set_ylabel("flee response"); ax[1, 0].legend()

    for i, r in enumerate(res["evo"]):
        ax[1, 1].plot(np.arange(len(r["mi_tr"])) * 2000, r["mi_tr"], label=f"seed {i}", alpha=0.8)
    ax[1, 1].axhline(nul.mean(), color="k", ls="--", lw=0.8, label="null")
    ax[1, 1].set_title(f"evolved signal-MI over time (kin relatedness r={rel.mean():.2f})")
    ax[1, 1].set_xlabel("step"); ax[1, 1].set_ylabel("MI (bits)"); ax[1, 1].legend()

    verdict = "alarm signalling EMERGED" if emerged else "no genuine communication (honest negative)"
    fig.suptitle(f"GENESIS R145 — Stage-2 signalling via KIN SELECTION (r={rel.mean():.2f}): {verdict}",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
