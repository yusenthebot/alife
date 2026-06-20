"""R154 — GENESIS MULTI-AXIS culture-gated PHYSICAL capabilities. R153 made culture gate ONE physical
action (what an agent can EAT). R154 generalises that to a multi-dimensional capability VECTOR: deep
tech-tree nodes ALSO unlock LOCOMOTION (a higher max speed, cap_level_step*1) and HARVEST REACH (a larger
eat radius, cap_level_step*2). So cultural depth reshapes the agent's whole physical phenotype — diet
(R153) + speed + reach — a tech-driven capability economy, not a single switch.

This run keeps BOTH axes live (tech_actions=True for diet, tech_capabilities=True for speed+reach), so the
integrated world has THREE culture-gated physical axes at once.

FALSIFIABLE claim + controls (in situ; never feed selection):
  (1) UNLOCKS — with social learning the population climbs to the deep capability nodes and physically
      realizes them: realized_axes rises, mean_speed_cap and mean_reach rise above the base phenotype.
  (2) PHYSICAL not scalar (load-bearing) — the locomotion node actually changes behaviour: the realized mean
      |velocity| of the social population is strictly higher than the asocial one (faster movement, not a number).
  (3) TRANSMISSION-REQUIRED (acid test) — the ASOCIAL control (learn=False) stays at the BASE phenotype:
      mean_speed_cap == cfg.speed and mean_reach == cfg.eat_radius EXACTLY (the deep nodes are unreachable
      from an empty repertoire in one lifetime — categorical, all-or-nothing).
  (4) MULTI-AXIS — diet (R153) is unlocked TOO (realized_tiers social > asocial): culture reshapes several
      physical axes at once, not just one.
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

OUT = "runs/r154_capabilities"
os.makedirs(OUT, exist_ok=True)
LOCKED = np.array([0.55, 0.15, 0.75])    # purple = base phenotype (no capability nodes)
UNLOCKED = np.array([1.0, 0.78, 0.10])   # gold = full physical capability (deep culture)


def cfg(**kw):
    # the viable building+combinatorial-culture regime; diet tiers shallow (R153), capability nodes DEEP
    # (cap_level_step=4 -> speed node level>=4, reach node level>=8) so only TRANSMISSION reaches them.
    base = dict(processing=True, building=True, culture=True, combinatorial=True, max_techniques=2000,
                n_seed_tech=6, innov_steps=1, hearth_reach_per_strength=3.0, hearth_radius=12.0,
                tech_actions=True, n_food_tiers=4, recipe_level_step=1, tier_value_bonus=2.0, tier0_frac=0.7,
                tech_capabilities=True, n_capabilities=2, cap_level_step=2, cap_speed_mult=1.0, cap_reach_mult=1.0,
                food_cap=1200, food_regrow=70, capacity=2000)
    base.update(kw)
    return replace(GenesisConfig(world=World3D(size=100.0), n0=600), **base)


def agent_color(w):
    """Colour each agent by its REALIZED CAPABILITY BREADTH — how many physical axes its culture has unlocked."""
    act = w.pop.active()
    if act.size == 0:
        return np.zeros((0, 3))
    held = w.rep[np.ix_(act, w._cap_tech)].sum(axis=1)               # 0..n_capabilities
    frac = (held / max(w.cfg.n_capabilities, 1))[:, None]            # 0=base, 1=full capability
    return LOCKED * (1.0 - frac) + UNLOCKED * frac


def trace(steps, seed, learn=True, every=40, render=False, render_every=120):
    w = GenesisWorld(cfg(learn=learn), seed=seed, evolve=True)
    st, ax_, sc, rc, rs, rt, pop = [], [], [], [], [], [], []
    frames = []
    r = None
    if render:
        from alife.render3d import Renderer3D
        r = Renderer3D(w.cfg.world, width=720, height=540)
    for s in range(steps):
        w.step()
        if s % every == 0:
            tc = w.tech_capabilities_test(); ta = w.tech_actions_test()
            st.append(s); ax_.append(tc.get("realized_axes", 0)); sc.append(tc.get("mean_speed_cap", 0.0))
            rc.append(tc.get("mean_reach", 0.0)); rs.append(tc.get("mean_realized_speed", 0.0))
            rt.append(ta.get("realized_tiers", 0)); pop.append(tc.get("n", 0))
        if render and s % render_every == 0:
            act = w.pop.active()
            if act.size:
                hp, _ = w.hearth_arrays()
                frames.append(r.render(w.pop.pos[act], w.pop.vel[act], agent_color(w),
                                       cam_angle=s * 0.012, cam_elev=0.42, food=hp))
    tc = w.tech_capabilities_test(); ta = w.tech_actions_test()
    out = dict(st=st, ax=ax_, sc=sc, rc=rc, rs=rs, rt=rt, pop=pop, cap=tc, act=ta)
    if render:
        r.ctx.release()
        if frames:
            imageio.mimsave(os.path.join(OUT, "capabilities.gif"), frames, fps=8, loop=0)
        out["frames"] = len(frames)
    return out


def mean_trace(runs, key):
    n = min(len(r[key]) for r in runs)
    return np.mean([r[key][:n] for r in runs], axis=0), runs[0]["st"][:n]


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 650
    cs = int(sys.argv[2]) if len(sys.argv) > 2 else 650
    seeds = (0, 1)
    t0 = time.time()
    print(f"=== headline social run ({steps} steps, capability-breadth-coloured 3D) ===", flush=True)
    h = trace(steps, seed=0, learn=True, render=True)
    hc = h["cap"]
    print(f"headline: pop {hc['n']} realized_axes {hc['realized_axes']}/{hc['n_axes']} "
          f"speed_cap {hc['mean_speed_cap']:.2f} reach {hc['mean_reach']:.2f} "
          f"realized_speed {hc['mean_realized_speed']:.2f} ({h.get('frames',0)} frames, {time.time()-t0:.0f}s)",
          flush=True)

    print(f"=== controls: social vs asocial, {len(seeds)} seeds, {cs} steps ===", flush=True)
    soc = [trace(cs, s, learn=True) for s in seeds]
    aso = [trace(cs, s, learn=False) for s in seeds]
    base_speed = GenesisWorld(cfg(), seed=0).cfg.speed
    base_reach = GenesisWorld(cfg(), seed=0).cfg.eat_radius
    for s, rr, ra in zip(seeds, soc, aso):
        cs_, ca = rr["cap"], ra["cap"]
        print(f"  seed {s}: SOCIAL axes {cs_['realized_axes']}/{cs_['n_axes']} speed_cap {cs_['mean_speed_cap']:.2f} "
              f"reach {cs_['mean_reach']:.2f} v {cs_['mean_realized_speed']:.2f} pop {cs_['n']} | "
              f"ASOCIAL axes {ca['realized_axes']} speed_cap {ca['mean_speed_cap']:.2f} reach {ca['mean_reach']:.2f} "
              f"v {ca['mean_realized_speed']:.2f} pop {ca['n']}", flush=True)

    def m(runs, fn):
        return float(np.mean([fn(r["cap"]) for r in runs]))
    soc_ax = m(soc, lambda c: c["realized_axes"]); aso_ax = m(aso, lambda c: c["realized_axes"])
    soc_sc = m(soc, lambda c: c["mean_speed_cap"]); aso_sc = m(aso, lambda c: c["mean_speed_cap"])
    soc_rc = m(soc, lambda c: c["mean_reach"]); aso_rc = m(aso, lambda c: c["mean_reach"])
    soc_rs = m(soc, lambda c: c["mean_realized_speed"]); aso_rs = m(aso, lambda c: c["mean_realized_speed"])
    soc_rt = float(np.mean([r["act"]["realized_tiers"] for r in soc]))
    aso_rt = float(np.mean([r["act"]["realized_tiers"] for r in aso]))
    print(f"  MEAN realized_axes: social {soc_ax:.2f} vs asocial {aso_ax:.2f} (max {soc[0]['cap']['n_axes']})", flush=True)
    print(f"  MEAN speed_cap: social {soc_sc:.2f} vs asocial {aso_sc:.2f} (base {base_speed})", flush=True)
    print(f"  MEAN reach: social {soc_rc:.2f} vs asocial {aso_rc:.2f} (base {base_reach})", flush=True)
    print(f"  MEAN realized_speed: social {soc_rs:.2f} vs asocial {aso_rs:.2f} (the locomotion node MOVES them faster)", flush=True)
    print(f"  MEAN realized_tiers (diet, R153): social {soc_rt:.2f} vs asocial {aso_rt:.2f}", flush=True)

    unlocks_axes = soc_ax > aso_ax + 0.5                              # transmission unlocks capability axes
    faster_cap = soc_sc > aso_sc + 0.3 and soc_rc > aso_rc + 0.3      # physical speed + reach rise
    physical_behaviour = soc_rs > aso_rs * 1.05                       # realized movement is actually faster (load-bearing)
    asocial_base = abs(aso_sc - base_speed) < 1e-6 and abs(aso_rc - base_reach) < 1e-6  # categorical: base phenotype
    multi_axis = soc_rt > aso_rt + 0.5                                # diet axis unlocked too (R153 still holds)
    verdict = unlocks_axes and faster_cap and physical_behaviour and asocial_base and multi_axis
    print(f"  CHECKS: unlocks-axes {unlocks_axes} | faster-cap {faster_cap} | physical-behaviour {physical_behaviour} "
          f"| asocial-base {asocial_base} | multi-axis {multi_axis}", flush=True)
    print(f"  VERDICT: {'MULTI-AXIS CULTURE-GATED CAPABILITIES' if verdict else 'NEGATIVE'}", flush=True)

    # ---- panel ----
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    s_ax, st = mean_trace(soc, "ax"); a_ax, _ = mean_trace(aso, "ax")
    ax[0, 0].plot(st, s_ax, color="#d6a000", lw=2, label="social")
    ax[0, 0].plot(st, a_ax, color="#999999", lw=2, label="asocial")
    ax[0, 0].set_title(f"REALIZED CAPABILITY AXES: social {soc_ax:.1f} vs asocial {aso_ax:.1f} (max {soc[0]['cap']['n_axes']})")
    ax[0, 0].set_xlabel("step"); ax[0, 0].set_ylabel("physical axes the population unlocks"); ax[0, 0].legend()
    s_sc, _ = mean_trace(soc, "sc"); a_sc, _ = mean_trace(aso, "sc")
    ax[0, 1].plot(st, s_sc, color="#d6a000", lw=2, label="social")
    ax[0, 1].plot(st, a_sc, color="#999999", lw=2, label="asocial")
    ax[0, 1].axhline(base_speed, color="#cc0000", ls="--", lw=1, label="base speed")
    ax[0, 1].set_title(f"MAX-SPEED CAP (locomotion): social {soc_sc:.2f} vs asocial {aso_sc:.2f}")
    ax[0, 1].set_xlabel("step"); ax[0, 1].set_ylabel("mean per-agent max speed"); ax[0, 1].legend()
    s_rc, _ = mean_trace(soc, "rc"); a_rc, _ = mean_trace(aso, "rc")
    ax[0, 2].plot(st, s_rc, color="#d6a000", lw=2, label="social")
    ax[0, 2].plot(st, a_rc, color="#999999", lw=2, label="asocial")
    ax[0, 2].axhline(base_reach, color="#cc0000", ls="--", lw=1, label="base reach")
    ax[0, 2].set_title(f"HARVEST REACH: social {soc_rc:.2f} vs asocial {aso_rc:.2f}")
    ax[0, 2].set_xlabel("step"); ax[0, 2].set_ylabel("mean per-agent eat radius"); ax[0, 2].legend()
    s_rs, _ = mean_trace(soc, "rs"); a_rs, _ = mean_trace(aso, "rs")
    ax[1, 0].plot(st, s_rs, color="#d6a000", lw=2, label="social")
    ax[1, 0].plot(st, a_rs, color="#999999", lw=2, label="asocial")
    ax[1, 0].set_title(f"REALIZED SPEED (load-bearing): social {soc_rs:.2f} vs asocial {aso_rs:.2f}\n(the locomotion node actually moves them faster)")
    ax[1, 0].set_xlabel("step"); ax[1, 0].set_ylabel("mean |velocity|"); ax[1, 0].legend()
    s_rt, _ = mean_trace(soc, "rt"); a_rt, _ = mean_trace(aso, "rt")
    ax[1, 1].plot(st, s_rt, color="#d6a000", lw=2, label="social")
    ax[1, 1].plot(st, a_rt, color="#999999", lw=2, label="asocial")
    ax[1, 1].set_title(f"DIET TIERS (R153 axis, multi-axis): social {soc_rt:.1f} vs asocial {aso_rt:.1f}")
    ax[1, 1].set_xlabel("step"); ax[1, 1].set_ylabel("food tiers unlocked"); ax[1, 1].legend()
    ax[1, 2].axis("off")
    vtxt = "MULTI-AXIS CULTURE-GATED CAPABILITIES" if verdict else "HONEST NEGATIVE"
    w0 = GenesisWorld(cfg(), seed=0)
    ax[1, 2].text(0.02, 0.95,
                  f"VERDICT: {vtxt}\n\n"
                  f"unlocks-axes: {unlocks_axes}\nfaster-cap: {faster_cap}\n"
                  f"physical-behaviour: {physical_behaviour}\nasocial-base: {asocial_base}\n"
                  f"multi-axis: {multi_axis}\n\n"
                  f"capability nodes (axis->tech, level):\n"
                  f"  speed -> {int(w0._cap_tech[0])} (L{int(w0._tree_level[w0._cap_tech[0]])})\n"
                  f"  reach -> {int(w0._cap_tech[1])} (L{int(w0._tree_level[w0._cap_tech[1]])})\n\n"
                  f"Mechanism: deep tech-tree nodes unlock PHYSICAL capabilities —\n"
                  f"a higher max speed (locomotion) and a larger eat radius (reach) —\n"
                  f"plus R153's diet. Cultural depth reshapes the whole phenotype;\n"
                  f"only TRANSMISSION reaches the deep nodes, so the asocial world\n"
                  f"is stuck at the base phenotype (speed/reach == base, exactly).",
                  fontsize=10, va="top", family="monospace")
    fig.suptitle(f"GENESIS R154 — MULTI-AXIS culture-gated PHYSICAL capabilities: techniques reshape movement + reach, not just diet.  {vtxt}\n"
                 f"(in capabilities.gif: purple=base phenotype, gold=full capability; the social world turns gold as nodes spread)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(OUT, "panel.png"), dpi=100)
    print(f"wrote {OUT}/capabilities.gif and {OUT}/panel.png  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
