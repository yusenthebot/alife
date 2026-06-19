"""R135 figure — Faraday waves: a vibrated surface erupts into a standing-wave lattice.

Top row: pattern gallery at three drive frequencies — shake faster, the lattice gets FINER.
Bottom row: (B) rms(t) growth above threshold vs flat sub-threshold control; (C) the surface
oscillates at the SUBHARMONIC Omega/2 (temporal FFT); (D) selected wavenumber k* tracks the
gravity-capillary dispersion w0(k*)=Omega/2.
GIF: the flat surface erupting into the breathing lattice.
"""

from __future__ import annotations

import os

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import replace

from alife.faraday import (FaradayConfig, run, dominant_k, resonant_k,
                           subharmonic_peak, w0)

OUT = "runs/r135_faraday"
os.makedirs(OUT, exist_ok=True)

BASE = FaradayConfig(N=96, steps=12000, seed=2)


def main():
    facs = [0.7, 1.0, 1.5]
    print("rendering pattern gallery (3 drive frequencies) ...")
    gallery = []
    for f in facs:
        c = replace(BASE, Omega=BASE.Omega * f)
        r = run(c)
        gallery.append((c, r["field"], dominant_k(r["field"], c), resonant_k(c)))
        print(f"  Omega x{f}: k_measured={gallery[-1][2]:.2f}  k*_theory={gallery[-1][3]:.2f}")

    print("running base case with time-series + GIF snapshots ...")
    base = run(BASE, sample_every=2, record_every=200)
    off = run(replace(BASE, a=0.2))
    peak = subharmonic_peak(base["series"], base["ts"])
    print(f"  rms x{base['rms'][-1] / base['rms'][0]:.0f}  subharmonic peak={peak:.2f} (Omega/2={BASE.Omega/2:.2f})")

    fig = plt.figure(figsize=(15, 9))
    # top row: pattern gallery, coarse -> fine
    for i, (c, fld, km, kt) in enumerate(gallery):
        ax = fig.add_subplot(2, 3, i + 1)
        v = np.abs(fld).max()
        ax.imshow(fld, cmap="RdBu_r", vmin=-v, vmax=v)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"drive Ω={c.Omega:.1f}  →  λ={'coarse' if i == 0 else 'fine' if i == 2 else 'medium'}\n"
                     f"k*={km:.2f} (theory {kt:.2f})", fontsize=10)

    axB = fig.add_subplot(2, 3, 4)
    tg = np.arange(len(base["rms"])) * BASE.dt * 20
    axB.semilogy(tg, base["rms"], color="#1f77b4", label=f"a={BASE.a} (driven) ×{base['rms'][-1]/base['rms'][0]:.0f}")
    axB.semilogy(tg, off["rms"], color="#999999", label="a=0.2 (sub-threshold)")
    axB.set_xlabel("time"); axB.set_ylabel("surface rms (log)")
    axB.set_title("B. Parametric onset: grows only above threshold"); axB.legend(fontsize=8)

    axC = fig.add_subplot(2, 3, 5)
    half = len(base["series"]) // 2
    s = base["series"][half:] - base["series"][half:].mean()
    dtc = float(base["ts"][1] - base["ts"][0])
    F = np.abs(np.fft.rfft(s * np.hanning(len(s)))); fr = np.fft.rfftfreq(len(s), d=dtc) * 2 * np.pi
    axC.plot(fr, F / F.max(), color="#2ca02c")
    axC.axvline(BASE.Omega / 2, color="#d62728", ls="--", label=f"Ω/2 = {BASE.Omega/2:.2f}")
    axC.axvline(BASE.Omega, color="#888", ls=":", label=f"Ω = {BASE.Omega:.2f} (drive)")
    axC.set_xlim(0, BASE.Omega * 1.4); axC.set_xlabel("response angular frequency")
    axC.set_ylabel("power"); axC.set_title(f"C. Subharmonic response (peak {peak:.2f})"); axC.legend(fontsize=8)

    axD = fig.add_subplot(2, 3, 6)
    oms = np.linspace(BASE.Omega * 0.6, BASE.Omega * 1.7, 40)
    kth = [resonant_k(replace(BASE, Omega=o)) for o in oms]
    axD.plot(kth, oms / 2, color="#1f77b4", label="dispersion ω0(k)=Ω/2")
    for c, fld, km, kt in gallery:
        axD.plot(km, c.Omega / 2, "o", color="#d62728", ms=9)
    axD.plot([], [], "o", color="#d62728", label="measured patterns")
    axD.set_xlabel("selected wavenumber k*"); axD.set_ylabel("Ω/2")
    axD.set_title("D. Wavelength tuned by drive frequency"); axD.legend(fontsize=8)

    fig.suptitle("R135 — Faraday waves: shaking a fluid makes a standing-wave lattice (subharmonic, drive-tuned)",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(f"{OUT}/faraday.png", dpi=110)
    print(f"wrote {OUT}/faraday.png")

    print("rendering eruption GIF ...")
    gfig, gax = plt.subplots(figsize=(5, 5))
    vmax = max(np.abs(snap).max() for snap in base["snaps"][len(base["snaps"]) // 2:])
    frames = []
    for k, snap in enumerate(base["snaps"]):
        gax.clear()
        gax.imshow(snap, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        gax.set_xticks([]); gax.set_yticks([])
        gax.set_title(f"Faraday surface  (t={k * 200 * BASE.dt:.1f})", fontsize=11)
        gfig.tight_layout(); gfig.canvas.draw()
        frames.append(np.asarray(gfig.canvas.buffer_rgba())[:, :, :3].copy())
    imageio.mimsave(f"{OUT}/faraday.gif", frames, fps=12, loop=0)
    print(f"wrote {OUT}/faraday.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
