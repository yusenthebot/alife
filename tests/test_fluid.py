import numpy as np

from alife.fluid import (equilibrium, macroscopic, poiseuille, karman, strouhal,
                         EX, EY, W, OPP)


def test_equilibrium_recovers_density_and_momentum():
    rho = np.full((4, 4), 1.3)
    ux = np.full((4, 4), 0.05); uy = np.full((4, 4), -0.02)
    feq = equilibrium(rho, ux, uy)
    r2, u2, v2 = macroscopic(feq)
    assert np.allclose(r2, rho) and np.allclose(u2, ux, atol=1e-6) and np.allclose(v2, uy, atol=1e-6)


def test_lattice_constants_consistent():
    assert abs(W.sum() - 1.0) < 1e-12                    # weights normalize
    assert (EX[OPP] == -EX).all() and (EY[OPP] == -EY).all()   # OPP reverses every direction


def test_poiseuille_is_parabolic():
    r = poiseuille(nx=16, ny=50, tau=0.8, force=1e-5, steps=5000)
    p, y = r["profile"], r["y"]
    assert p[0] < 1e-6 and p[-1] < 1e-6                  # no-slip at the walls
    assert p.argmax() in range(20, 30)                   # peak at the channel centre
    # peak-normalized profile matches the analytic parabola shape
    rmse = np.sqrt(np.mean((p / p.max() - r["analytic"] / r["analytic"].max()) ** 2))
    assert rmse < 0.03


def test_karman_sheds_vortices_with_right_strouhal():
    k = karman(nx=300, ny=80, tau=0.55, u_in=0.1, radius=9, steps=12000)
    assert 60 < k["Re"] < 160                            # vortex-shedding regime
    assert k["probe"].std() > 0.01                       # oscillating wake = shedding
    st = strouhal(k["probe"], k["radius"], k["u_in"])
    assert 0.10 < st < 0.30                              # Strouhal in the expected band


def test_flow_is_stable_not_blown_up():
    k = karman(nx=240, ny=70, tau=0.55, u_in=0.1, radius=8, steps=4000)
    assert np.isfinite(k["ux"]).all() and np.nanmax(np.abs(k["ux"])) < 0.5   # bounded velocities


def test_viscosity_positive():
    # tau > 0.5 gives positive kinematic viscosity nu=(tau-0.5)/3
    r = poiseuille(nx=10, ny=30, tau=0.7, force=1e-5, steps=500)
    assert r["nu"] > 0
