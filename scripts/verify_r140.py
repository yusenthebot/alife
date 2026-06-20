"""R140 review-round adversarial re-verification.

Re-run each R131-R139 headline with FRESH seeds the unit tests never used (tests use
{0,1,2,3,4,7,11}; here we use primes >=41). A headline only "survives" if its signature
reproduces on an unseen seed. Honest: any FAIL is reported, not hidden. Sequential, one
process, arrays freed between models (64GB host, no concurrent sims).
"""

from __future__ import annotations

import gc

import numpy as np

PASS, FAIL = [], []


def check(name, ok, detail):
    (PASS if ok else FAIL).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# ---------- R131 Barkley excitable media ----------
def r131():
    from alife.barkley import BarkleyConfig, run_spiral, run_target, ring_count
    r = run_spiral(BarkleyConfig(N=160, steps=4000, seed=41))
    check("R131 spiral re-entrant (activity>0.05)", r["activity"] > 0.05, f"activity={r['activity']:.3f}")
    rt = run_target(BarkleyConfig(N=200, steps=4500, seed=43), pace_period=350)
    nr = ring_count(rt["u"])
    check("R131 target rings (>=2)", nr >= 2, f"rings={nr}")
    del r, rt


# ---------- R132 Wolf-Sheep-Grass ----------
def r132():
    from alife.wolfsheep import WolfSheepConfig, run, coexists
    for s in (47, 53):
        r = run(WolfSheepConfig(steps=2500, seed=s))
        co = coexists(r) and r["grass"][-1] > 0
        w = r["wolves"][400:].astype(float)
        cv = w.std() / max(w.mean(), 1e-9)
        check(f"R132 coexist+oscillate seed={s}", co and cv > 0.2, f"coexist={co} wolf_cv={cv:.2f}")
        del r


# ---------- R133 Termite stigmergy ----------
def r133():
    from alife.termites import TermiteConfig, run, clustering
    on = clustering(run(TermiteConfig(steps=3000, k=6.0, seed=59))["M"])
    off = clustering(run(TermiteConfig(steps=3000, k=0.0, seed=59))["M"])
    check("R133 stigmergy clusters (>2.5) vs random (<1.5)", on > 2.5 and off < 1.5, f"k=6:{on:.2f} k=0:{off:.2f}")


# ---------- R134 Murmuration predator evasion ----------
def r134():
    from alife.murmuration import MurmurConfig, run
    from dataclasses import replace
    base = MurmurConfig(N=140, steps=800, seed=61)
    on = run(base)["catches"]
    off = run(replace(base, flee=0.0))["catches"]
    check("R134 fleeing protects flock (off>10x on)", off > 10 * max(on, 1), f"on_catches={on} off_catches={off}")


# ---------- R135 Faraday subharmonic ----------
def r135():
    from alife.faraday import FaradayConfig, run, dominant_k, resonant_k, subharmonic_peak
    base = FaradayConfig(N=64, Lx=2 * np.pi * 5, steps=6500, seed=67)
    r = run(base, sample_every=2)
    kstar = resonant_k(base)
    kd = dominant_k(r["field"], base)
    peak = subharmonic_peak(r["series"], r["ts"])
    check("R135 wavelength matches resonance", abs(kd - kstar) < 0.12 * kstar, f"k={kd:.3f} k*={kstar:.3f}")
    check("R135 response subharmonic (~Omega/2)", abs(peak - base.Omega / 2) < 0.2 * (base.Omega / 2), f"peak={peak:.3f} Om/2={base.Omega/2:.3f}")
    del r


# ---------- R136 Grain growth power-law coarsening ----------
def r136():
    from alife.graingrowth import GrainConfig, run, coarsening_exponent
    from dataclasses import replace
    base = GrainConfig(L=100, Q=64, T=0.6, steps=120, seed=71)
    log = [5, 15, 40, 120]
    r = run(base, log_at=log)
    eb = coarsening_exponent(r["t"], r["bond"])
    eg = coarsening_exponent(r["t"], r["ngrains"])
    check("R136 power-law coarsening (eb<-0.25, eg<-0.5)", eb < -0.25 and eg < -0.5, f"eb={eb:.2f} eg={eg:.2f}")
    g = run(replace(base, greedy=True), log_at=log)
    check("R136 greedy pins (no coarsen)", g["bond"][-1] > 0.9 * g["bond"][1], f"bond_end/bond1={g['bond'][-1]/g['bond'][1]:.2f}")
    del r, g


# ---------- R137 Fisher-KPP front (deterministic PDE: theory robustness) ----------
def r137():
    from alife.fisherfront import FrontConfig, run1d, run2d, fisher_speed_theory
    c = FrontConfig(r=1.0, D=1.0)
    sp = run1d(c)["speed"]
    th = fisher_speed_theory(c)
    check("R137 Fisher speed ~2sqrt(rD)", abs(sp - th) < 0.12 * th and sp < th, f"c={sp:.3f} theory={th:.3f}")
    inv = run1d(FrontConfig(allee=0.3))["speed"]
    ext = run1d(FrontConfig(allee=0.7))["speed"]
    check("R137 Allee threshold sign-change", inv > 0.05 and ext < -0.05, f"a=0.3:{inv:.3f} a=0.7:{ext:.3f}")
    r2 = run2d(FrontConfig(), N=140, steps=800, seed_radius=15)
    check("R137 2D colony invades", r2["radius"][-1] > 1.5 * r2["radius"][0], f"R0={r2['radius'][0]:.1f} R1={r2['radius'][-1]:.1f}")
    del r2


# ---------- R138 Turing on a sphere ----------
def r138():
    from alife.turingsphere import TuringSphereConfig, run, count_spots
    from dataclasses import replace
    base = TuringSphereConfig(subdiv=4, F=0.0367, k=0.0649, steps=9000, seed=73)
    small_r = run(base)
    small = count_spots(small_r["v"], small_r["A"])
    check("R138 pattern forms (spots>5, isolated)", small > 5 and (small_r["v"] > 0.2).mean() < 0.2,
          f"spots={small} cover={(small_r['v']>0.2).mean():.2f}")
    big_r = run(replace(base, subdiv=5))
    big = count_spots(big_r["v"], big_r["A"])
    check("R138 more spots on bigger sphere", big > 1.5 * small, f"small={small} big={big}")
    del small_r, big_r


# ---------- R139 Dendritic solidification ----------
def r139():
    from alife.dendrite import DendriteConfig, run, arm_count, solid_fraction
    from dataclasses import replace
    base = DendriteConfig(N=150, steps=1800, seed=79)
    a6 = arm_count(run(replace(base, j=6))["p"])
    a4 = arm_count(run(replace(base, j=4))["p"])
    check("R139 arm count = anisotropy mode j", a6 == 6 and a4 == 4, f"j=6->{a6} j=4->{a4}")
    fast = solid_fraction(run(replace(base, delta=0.04))["p"])
    slow = solid_fraction(run(replace(base, delta=0.0))["p"])
    check("R139 anisotropy drives growth (>2x)", fast > 2 * slow, f"delta0.04:{fast:.3f} delta0:{slow:.3f}")


for fn in (r131, r132, r133, r134, r135, r136, r137, r138, r139):
    print(f"\n=== {fn.__name__} ===")
    try:
        fn()
    except Exception as e:  # noqa: BLE001 -- a crash on a fresh seed IS a finding
        check(f"{fn.__name__} (no crash)", False, f"EXCEPTION {type(e).__name__}: {e}")
    gc.collect()

print(f"\n{'=' * 50}\nSURVIVED: {len(PASS)}   FAILED: {len(FAIL)}")
if FAIL:
    print("FAILS:", FAIL)
