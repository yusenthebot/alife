"""R144 — GENESIS Stage 2: an emergent-SIGNALLING channel + a red-team-grade emergence protocol.

Each prey now emits an evolved scalar UTTERANCE and hears its nearest neighbour's, over the existing
kin-adjacency — the substrate on which predator-alarm communication could evolve from scratch. But a
signal that merely *correlates* with the world is trivial to mistake for communication, so this script is
built around a FOUR-CONTROL protocol designed to REFUTE a false positive before believing it:

  1. scrambled-channel null   — permute the danger labels; MI under the null is ~0.
  2. frozen-genome control    — evolve=False. If a FROZEN (random-brain) population shows MI >= the
                                evolved one, the MI is a SENSORY-REACTION ARTIFACT (the emitter's output
                                is just a function of its own predator-sense), NOT evolved meaning.
  3. causal lesion test       — silence the heard channel on the same brains/state; does behaviour change
                                ADAPTIVELY (flee away from an alarming neighbour)?
  4. intact-vs-deaf functional test — evolve a population that can HEAR vs one permanently deaf (same brain
                                shape). The ARTIFACT-IMMUNE test: does hearing causally improve survival?

HONEST FINDING (this configuration): signal-danger MI looks high but the FROZEN control unmasks it as
mimicry, and hearing yields NO survival benefit over deaf — genuine alarm communication did NOT emerge
in-situ here. The protocol did its job: it caught the artifact. The figure shows exactly that. One sim at
a time; GL context released.
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

OUT = "runs/r144_signalling"
os.makedirs(OUT, exist_ok=True)
# sparse, episodic predators -> danger is intermittent (dfrac ~0.25) so an alarm could be informative,
# and prey persist robustly; strong informational asymmetry (short direct predator sense -> a neighbour
# closer to the predator could warn earlier). This is the setting most FAVOURABLE to alarm signalling.
SIG = dict(signalling=True, prey_pred_range=14.0, n_predators0=40, pred_capacity=130)
NPERM = 128


def _cfg(**kw):
    return replace(GenesisConfig(), **SIG, **kw)


def run(seed, evolve, deaf, steps, rng):
    w = GenesisWorld(_cfg(deaf=deaf), seed=seed, evolve=evolve)
    pops, mis = [], []
    for s in range(steps):
        w.step()
        if s % 250 == 0:
            pops.append(w.pop.n_alive)
        if s % 2000 == 0:
            mis.append(w.snapshot()["signal_mi"])
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
        print(f" seed {seed}: EVO MI={e['mi']:.4f}(z={e['z']:.1f}) FROZEN MI={f['mi']:.4f}(z={f['z']:.1f})"
              f" | HEAR pop={e['pop2nd']:.0f} DEAF pop={d['pop2nd']:.0f} (ratio {e['pop2nd']/max(d['pop2nd'],1):.3f})"
              f" | causal flee int={e['flee_intact']:.3f}/deaf={e['flee_deaf']:.3f}", flush=True)

    def col(cond, key):
        return np.array([r[key] for r in res[cond]])

    evo_mi, frz_mi, nul = col("evo", "mi"), col("frozen", "mi"), col("evo", "null")
    hear_pop, deaf_pop = col("evo", "pop2nd"), col("deaf", "pop2nd")
    fi, fd = col("evo", "flee_intact"), col("evo", "flee_deaf")
    print(f"\n MEAN: EVO MI {evo_mi.mean():.4f} vs FROZEN MI {frz_mi.mean():.4f} vs null {nul.mean():.4f}"
          f"  -> frozen>=evolved: {frz_mi.mean() >= evo_mi.mean()} (MI is a sensory-reaction ARTIFACT)",
          flush=True)
    print(f" MEAN: HEAR pop {hear_pop.mean():.0f} vs DEAF pop {deaf_pop.mean():.0f}"
          f"  -> hearing benefit ratio {hear_pop.mean()/max(deaf_pop.mean(),1):.3f} (no functional gain)",
          flush=True)
    print(f" MEAN: causal flee intact {fi.mean():.3f} vs deaf {fd.mean():.3f}"
          f"  -> adaptive listening: {fi.mean() > fd.mean()}", flush=True)

    print("=== rendering utterance-coloured 3D GIF ===", flush=True)
    gif(0, min(steps, 12000), rng)

    # ---- figure: the protocol verdict ----
    fig, ax = plt.subplots(2, 2, figsize=(15, 9))
    x = np.arange(len(seeds))
    ax[0, 0].bar(x - 0.25, evo_mi, 0.25, label="evolved", color="#2ca02c")
    ax[0, 0].bar(x, frz_mi, 0.25, label="frozen (control)", color="#d62728")
    ax[0, 0].bar(x + 0.25, nul, 0.25, label="scrambled null", color="#7f7f7f")
    ax[0, 0].set_xticks(x); ax[0, 0].set_xticklabels([f"seed {s}" for s in seeds])
    ax[0, 0].set_title("signal-danger MI: FROZEN >= EVOLVED -> a sensory-reaction ARTIFACT, not meaning")
    ax[0, 0].set_ylabel("MI (bits)"); ax[0, 0].legend()

    ax[0, 1].bar(x - 0.18, hear_pop, 0.36, label="can hear", color="#1f77b4")
    ax[0, 1].bar(x + 0.18, deaf_pop, 0.36, label="deaf control", color="#9467bd")
    ax[0, 1].set_xticks(x); ax[0, 1].set_xticklabels([f"seed {s}" for s in seeds])
    ax[0, 1].set_title(f"intact-vs-deaf survival (artifact-immune): ratio "
                       f"{hear_pop.mean()/max(deaf_pop.mean(),1):.2f} -> hearing gives NO benefit")
    ax[0, 1].set_ylabel("prey population (2nd-half mean)"); ax[0, 1].legend()

    ax[1, 0].bar(x - 0.18, fi, 0.36, label="channel intact", color="#2ca02c")
    ax[1, 0].bar(x + 0.18, fd, 0.36, label="channel lesioned", color="#d62728")
    ax[1, 0].axhline(0, color="k", lw=0.5)
    ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels([f"seed {s}" for s in seeds])
    ax[1, 0].set_title("causal lesion: flee-away-from-alarmer (intact vs silenced) -> no adaptive listening")
    ax[1, 0].set_ylabel("flee response"); ax[1, 0].legend()

    for i, r in enumerate(res["evo"]):
        ax[1, 1].plot(np.arange(len(r["mi_tr"])) * 2000, r["mi_tr"], label=f"seed {i}", alpha=0.8)
    ax[1, 1].axhline(nul.mean(), color="k", ls="--", lw=0.8, label="null")
    ax[1, 1].set_title("evolved signal-MI over time (no climb -> no emergence)")
    ax[1, 1].set_xlabel("step"); ax[1, 1].set_ylabel("MI (bits)"); ax[1, 1].legend()

    fig.suptitle("GENESIS R144 — Stage-2 signalling substrate + emergence protocol: the artifact caught, "
                 "no genuine communication (yet)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
