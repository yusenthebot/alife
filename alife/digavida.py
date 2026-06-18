"""R51 — Digital Genesis: evolution of self-replicating programs (Avida/Tierra).

Every earlier round shared one substrate: a fixed vector of floats interpreted by
a human-written update rule. Here the genome IS a program — a sequence of CPU
instructions — and evolution rewrites the code itself. A hand-seeded ancestor is a
little program that copies its own instructions into a fresh block of memory and
divides; running it in a finite "soup" with copy-errors, mutations accumulate and
natural selection acts on raw executable code. Faster replicators (often shorter
genomes) out-reproduce the rest with nothing optimized by hand. This is the
substrate of Tierra (Ray 1991) and Avida (Ofria & Wilke), where, in later stages,
de-novo computation and parasites evolve from a pure copier.

Stage 1 (this round): a genuine self-replicator that fills the soup, copy-mutations
accumulate, and selection for replication speed shrinks the genome — verified by
disassembling and single-stepping an *evolved* organism's CPU.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# --- instruction set (small, head-based copy loop; templates kept simple) ---
NOP, ALLOC, LOADLEN, SETFLOW, COPY, DEC, JMPZBACK, DIVIDE, INC, SWAP, NAND, PUSH, POP, IFZ = range(14)
N_OPS = 14
NAMES = ["nop", "alloc", "loadlen", "setflow", "copy", "dec", "jnz", "divide",
         "inc", "swap", "nand", "push", "pop", "ifz"]
MASK = 0xFFFFFFFF

# the hand-written ancestor: allocate, set loop counter = genome length, copy that
# many instructions one at a time, then divide. A genuine self-replicator.
ANCESTOR = np.array([ALLOC, LOADLEN, SETFLOW, COPY, DEC, JMPZBACK, DIVIDE], dtype=np.int64)

MIN_LEN, MAX_LEN = 5, 80
MAX_CYCLES = 400          # reap an organism that runs this long without dividing


@dataclass
class CPU:
    ip: int = 0
    a: int = 0
    b: int = 0
    c: int = 0
    read: int = 0
    write: int = 0
    flow: int = 0
    off: list = field(default_factory=list)
    stack: list = field(default_factory=list)
    cycles: int = 0


def disassemble(genome) -> str:
    return " ".join(NAMES[int(o) % N_OPS] for o in genome)


def step(genome: np.ndarray, cpu: CPU, rng, mut: float):
    """Execute one instruction. Returns the finished offspring genome on a valid
    divide, else None."""
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
                instr = int(rng.integers(0, N_OPS))     # copy error -> point mutation
            cpu.off.append(instr); cpu.read += 1; cpu.write += 1
    elif op == DEC:
        cpu.a -= 1
    elif op == INC:
        cpu.a += 1
    elif op == JMPZBACK:                                  # jump to flow while a != 0
        if cpu.a != 0:
            cpu.ip = cpu.flow; jumped = True
    elif op == DIVIDE:
        if MIN_LEN <= len(cpu.off) <= MAX_LEN:
            spawned = np.array(cpu.off, dtype=np.int64)
        cpu.off = []; cpu.read = 0; cpu.write = 0        # reset copy state either way
    elif op == SWAP:
        cpu.a, cpu.b = cpu.b, cpu.a
    elif op == NAND:
        cpu.a = (~(cpu.b & cpu.c)) & MASK
    elif op == PUSH:
        if len(cpu.stack) < 16:
            cpu.stack.append(cpu.a)
    elif op == POP:
        cpu.a = cpu.stack.pop() if cpu.stack else 0
    elif op == IFZ:
        if cpu.a != 0:
            cpu.ip = (cpu.ip + 1) % n                     # skip next instruction
    if not jumped:
        cpu.ip = (cpu.ip + 1) % n
    cpu.cycles += 1
    return spawned


def replicate_once(genome: np.ndarray, mut: float = 0.0, seed: int = 0, max_steps: int = 2000):
    """Run an isolated genome until it first divides; return (offspring, n_cycles).
    Returns (None, cycles) if it never divides within max_steps."""
    rng = np.random.default_rng(seed)
    cpu = CPU()
    for _ in range(max_steps):
        out = step(genome, cpu, rng, mut)
        if out is not None:
            return out, cpu.cycles
    return None, cpu.cycles


def is_replicator(genome: np.ndarray) -> bool:
    """Does this genome produce a viable offspring on its own (no mutation)?"""
    off, _ = replicate_once(genome, mut=0.0)
    return off is not None and MIN_LEN <= len(off) <= MAX_LEN


def padded_ancestor(length: int) -> np.ndarray:
    """The ancestor padded with trailing NOPs — a slow replicator that selection
    can streamline (every NOP is a wasted CPU cycle each replication)."""
    pad = max(0, length - len(ANCESTOR))
    return np.concatenate([ANCESTOR, np.full(pad, NOP, dtype=np.int64)])


@dataclass
class SoupConfig:
    n_slots: int = 200
    seed_len: int = 30          # padded ancestor length to start
    n_seed: int = 8
    sweeps: int = 2500
    mut_point: float = 0.02     # per-copied-instruction point mutation
    mut_indel: float = 0.015    # per-divide insertion/deletion
    record_every: int = 25


def _indel(off: np.ndarray, rng, p: float) -> np.ndarray:
    if rng.random() < p and len(off) > MIN_LEN:
        i = int(rng.integers(0, len(off)))
        off = np.delete(off, i)
    if rng.random() < p and len(off) < MAX_LEN:
        i = int(rng.integers(0, len(off) + 1))
        off = np.insert(off, i, int(rng.integers(0, N_OPS)))
    return off


def run_soup(cfg: SoupConfig, seed: int = 0):
    rng = np.random.default_rng(seed)
    genomes: list = [None] * cfg.n_slots
    cpus: list = [None] * cfg.n_slots
    for i in range(cfg.n_seed):
        genomes[i] = padded_ancestor(cfg.seed_len)
        cpus[i] = CPU()
    hist = {"t": [], "pop": [], "mean_len": [], "diversity": [], "divisions": []}
    total_div = 0

    def place(child):
        empties = [i for i in range(cfg.n_slots) if genomes[i] is None]
        slot = empties[0] if empties else int(rng.integers(0, cfg.n_slots))
        genomes[slot] = child
        cpus[slot] = CPU()

    for sweep in range(cfg.sweeps):
        for i in range(cfg.n_slots):
            g = genomes[i]
            if g is None:
                continue
            child = step(g, cpus[i], rng, cfg.mut_point)
            if child is not None:
                child = _indel(child, rng, cfg.mut_indel)
                if is_replicator(child) or rng.random() < 0.5:   # broken kids may still take a slot (then die out)
                    place(child)
                cpus[i].cycles = 0          # parent keeps living, copy state reset
                total_div += 1
            elif cpus[i].cycles > MAX_CYCLES:
                genomes[i] = None; cpus[i] = None     # reap a stalled organism
        if sweep % cfg.record_every == 0:
            alive = [g for g in genomes if g is not None]
            if not alive:
                break
            lens = [len(g) for g in alive]
            uniq = len({g.tobytes() for g in alive})
            hist["t"].append(sweep)
            hist["pop"].append(len(alive))
            hist["mean_len"].append(float(np.mean(lens)))
            hist["diversity"].append(uniq)
            hist["divisions"].append(total_div)
    alive = [g for g in genomes if g is not None]
    out = {k: np.array(v, dtype=float) for k, v in hist.items()}
    out["final_genomes"] = alive
    return out


def compete(len_short: int, len_long: int, n_slots: int = 200, n_each: int = 20,
            sweeps: int = 3000, record_every: int = 50, seed: int = 0):
    """Seed equal numbers of two replicator lengths (no mutation) and track how the
    faster (shorter) one out-reproduces the slower — selection for replication speed."""
    rng = np.random.default_rng(seed)
    gs = padded_ancestor(len_short); gl = padded_ancestor(len_long)
    genomes: list = [None] * n_slots; cpus: list = [None] * n_slots
    for i in range(n_each):
        genomes[2 * i] = gs.copy(); cpus[2 * i] = CPU()
        genomes[2 * i + 1] = gl.copy(); cpus[2 * i + 1] = CPU()

    def place(child):
        e = [i for i in range(n_slots) if genomes[i] is None]
        s = e[0] if e else int(rng.integers(0, n_slots))
        genomes[s] = child; cpus[s] = CPU()

    hist = {"t": [], "short": [], "long": []}
    for sweep in range(sweeps):
        for i in range(n_slots):
            if genomes[i] is None:
                continue
            ch = step(genomes[i], cpus[i], rng, 0.0)
            if ch is not None:
                place(ch); cpus[i].cycles = 0
            elif cpus[i].cycles > MAX_CYCLES:
                genomes[i] = None; cpus[i] = None
        if sweep % record_every == 0:
            alive = [g for g in genomes if g is not None]
            hist["t"].append(sweep)
            hist["short"].append(sum(1 for g in alive if len(g) == len_short))
            hist["long"].append(sum(1 for g in alive if len(g) == len_long))
    return {k: np.array(v, dtype=float) for k, v in hist.items()}

