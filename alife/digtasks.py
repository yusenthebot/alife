"""R52 — Digital Genesis Stage 2: computation evolves because it PAYS.

R51 gave self-replicating programs. Here the environment rewards computation: each
organism is born with two input numbers; if it OUTPUTs a boolean function of them
(NOT, NAND, AND, ...), it earns MERIT, and merit buys CPU cycles — so a computing
organism replicates faster than a pure copier. Nothing instructs the population to
compute; selection does, because computation pays for itself in replication speed.

This round proves the engine: a hand-written computing replicator (it does NAND on
its inputs each cycle) genuinely out-reproduces an identical-length pure copier
purely through the merit it earns. (De-novo origin of tasks from a pure copier is
the harder frontier — the minimal ISA makes the 4-instruction task motif a needle
in a haystack; reported honestly, it is the target of the EQU round to come.)

Clean ISA: INA->reg b=input1, INB->reg c=input2, NAND->a=~(b&c), OUT->check a.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from alife.digavida import (
    ALLOC, LOADLEN, SETFLOW, COPY, DEC, JMPZBACK, DIVIDE, INC, SWAP, NAND, PUSH, POP, IFZ,
    ANCESTOR, MIN_LEN, MAX_LEN, MASK,
)

INA, INB, OUT = 14, 15, 16
N_OPS_T = 17
NAMES_T = ["nop", "alloc", "loadlen", "setflow", "copy", "dec", "jnz", "divide",
           "inc", "swap", "nand", "push", "pop", "ifz", "ina", "inb", "out"]

TASKS = [
    ("NOT", lambda a, b: (~a) & MASK, 2.0),
    ("NAND", lambda a, b: (~(a & b)) & MASK, 2.0),
    ("AND", lambda a, b: (a & b) & MASK, 4.0),
    ("ORN", lambda a, b: (a | (~b)) & MASK, 4.0),
    ("OR", lambda a, b: (a | b) & MASK, 8.0),
    ("ANDN", lambda a, b: (a & (~b)) & MASK, 8.0),
    ("NOR", lambda a, b: (~(a | b)) & MASK, 16.0),
    ("XOR", lambda a, b: (a ^ b) & MASK, 16.0),
    ("EQU", lambda a, b: (~(a ^ b)) & MASK, 32.0),
]


@dataclass
class CPUT:
    ip: int = 0
    a: int = 0
    b: int = 0
    c: int = 0
    read: int = 0
    write: int = 0
    flow: int = 0
    i1: int = 0
    i2: int = 0
    off: list = field(default_factory=list)
    tasks: set = field(default_factory=set)
    merit: float = 1.0
    cycles: int = 0


def disasm_t(genome) -> str:
    return " ".join(NAMES_T[int(o) % N_OPS_T] for o in genome)


def step_t(genome, cpu: CPUT, rng, mut, task_counts):
    n = len(genome)
    op = int(genome[cpu.ip % n])
    jumped = False
    spawned = None
    if op == ALLOC:
        cpu.off = []; cpu.read = 0; cpu.write = 0
    elif op == LOADLEN:
        cpu.a = n
    elif op == SETFLOW:
        cpu.flow = cpu.ip
    elif op == COPY:
        if cpu.write < MAX_LEN:
            instr = int(genome[cpu.read % n])
            if rng.random() < mut:
                instr = int(rng.integers(0, N_OPS_T))
            cpu.off.append(instr); cpu.read += 1; cpu.write += 1
    elif op == DEC:
        cpu.a = (cpu.a - 1) & MASK
    elif op == INC:
        cpu.a = (cpu.a + 1) & MASK
    elif op == JMPZBACK:
        if cpu.a != 0:
            cpu.ip = cpu.flow; jumped = True
    elif op == DIVIDE:
        if MIN_LEN <= len(cpu.off) <= MAX_LEN:
            spawned = np.array(cpu.off, dtype=np.int64)
        cpu.off = []; cpu.read = 0; cpu.write = 0
    elif op == SWAP:
        cpu.a, cpu.b = cpu.b, cpu.a
    elif op == NAND:
        cpu.a = (~(cpu.b & cpu.c)) & MASK
    elif op == PUSH:
        pass
    elif op == POP:
        pass
    elif op == IFZ:
        if cpu.a != 0:
            cpu.ip = (cpu.ip + 1) % n
    elif op == INA:
        cpu.b = cpu.i1
    elif op == INB:
        cpu.c = cpu.i2
    elif op == OUT:
        out = cpu.a & MASK
        for name, fn, bonus in TASKS:
            if name not in cpu.tasks and out == fn(cpu.i1, cpu.i2):
                cpu.tasks.add(name); cpu.merit *= bonus
                task_counts[name] = task_counts.get(name, 0) + 1
    if not jumped:
        cpu.ip = (cpu.ip + 1) % n
    cpu.cycles += 1
    return spawned


# a hand-written computing replicator: copies itself AND does NAND on its inputs
TASK_DOER = np.array([ALLOC, LOADLEN, SETFLOW, COPY, DEC, JMPZBACK, DIVIDE,
                      INA, INB, NAND, OUT], dtype=np.int64)


def _fresh_cpu(rng) -> CPUT:
    return CPUT(i1=int(rng.integers(0, 1 << 32)), i2=int(rng.integers(0, 1 << 32)))


def does_task(genome, seed=0, max_steps=3000):
    """Run a genome in isolation across several replication cycles; return the set of
    logic tasks it performs (task code typically runs between divisions)."""
    rng = np.random.default_rng(seed)
    cpu = _fresh_cpu(rng)
    tc = {}
    for _ in range(max_steps):
        step_t(genome, cpu, rng, 0.0, tc)
    return cpu.tasks


def pure_copier(length: int) -> np.ndarray:
    pad = max(0, length - len(ANCESTOR))
    return np.concatenate([ANCESTOR, np.full(pad, 0, dtype=np.int64)])


def _run_soup(genomes, cpus, n_slots, sweeps, mut, rng, max_inst=10, max_cycles=800,
              record_every=50, tracker=None):
    cum = {}

    def place(child):
        e = [i for i in range(n_slots) if genomes[i] is None]
        s = e[0] if e else int(rng.integers(0, n_slots))
        genomes[s] = child; cpus[s] = _fresh_cpu(rng)

    hist = []
    for sweep in range(sweeps):
        for i in range(n_slots):
            if genomes[i] is None:
                continue
            for _ in range(min(max_inst, max(1, int(round(cpus[i].merit))))):
                ch = step_t(genomes[i], cpus[i], rng, mut, cum)
                if ch is not None:
                    place(ch); cpus[i].cycles = 0
                    break
            if genomes[i] is not None and cpus[i].cycles > max_cycles:
                genomes[i] = None; cpus[i] = None
        if sweep % record_every == 0:
            alive_g = [g for g in genomes if g is not None]
            if not alive_g:
                break
            hist.append(tracker(sweep, genomes, cpus, cum))
    return hist, cum


def compete_compute(n_slots=200, n_each=20, sweeps=2500, seed=0):
    """Hand-written NAND computer vs equal-length pure copier (no mutation): does the
    merit from computing make the computer out-reproduce the copier?"""
    rng = np.random.default_rng(seed)
    genomes = [None] * n_slots; cpus = [None] * n_slots
    doer = TASK_DOER; copier = pure_copier(len(TASK_DOER))
    for k in range(n_each):
        genomes[2 * k] = doer.copy(); cpus[2 * k] = _fresh_cpu(rng)
        genomes[2 * k + 1] = copier.copy(); cpus[2 * k + 1] = _fresh_cpu(rng)

    def track(sweep, gs, cs, cum):
        alive = [g for g in gs if g is not None]
        nd = sum(1 for g in alive if len(g) == len(doer) and np.array_equal(g, doer))
        nc = sum(1 for g in alive if np.array_equal(g, copier))
        return (sweep, nd, nc)

    hist, _ = _run_soup(genomes, cpus, n_slots, sweeps, 0.0, rng, tracker=track)
    arr = np.array(hist, dtype=float)
    return {"t": arr[:, 0], "computers": arr[:, 1], "copiers": arr[:, 2]}


def run_denovo(n_slots=200, n_seed=12, seed_len=20, sweeps=8000, mut=0.03, seed=0):
    """Seed only pure copiers and let mutation search for task code (de-novo origin)."""
    rng = np.random.default_rng(seed)
    genomes = [None] * n_slots; cpus = [None] * n_slots
    for i in range(n_seed):
        genomes[i] = pure_copier(seed_len); cpus[i] = _fresh_cpu(rng)

    def track(sweep, gs, cs, cum):
        alive = [c for c in cs if c is not None]
        frac = np.mean([1.0 if c.tasks else 0.0 for c in alive]) if alive else 0.0
        return (sweep, len(alive), frac, len(cum))

    hist, cum = _run_soup(genomes, cpus, n_slots, sweeps, mut, rng, tracker=track)
    arr = np.array(hist, dtype=float)
    return {"t": arr[:, 0], "pop": arr[:, 1], "task_frac": arr[:, 2], "n_task_types": arr[:, 3],
            "cum_tasks": cum}
