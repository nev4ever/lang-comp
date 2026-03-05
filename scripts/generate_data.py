#!/usr/bin/env python3
import argparse
import random
from pathlib import Path

VOCAB = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "omicron",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
    "benchmark",
    "runtime",
    "compiler",
    "interpreter",
    "thread",
    "memory",
    "cache",
    "kernel",
    "vector",
    "matrix",
    "string",
    "token",
    "parser",
    "stream",
    "network",
    "filesystem",
    "latency",
    "throughput",
    "binary",
    "source",
    "module",
    "package",
    "function",
    "closure",
    "object",
    "class",
    "method",
    "generic",
    "template",
    "pointer",
    "array",
    "slice",
    "hash",
    "map",
    "queue",
    "stack",
    "graph",
    "tree",
    "node",
    "edge",
    "prime",
    "sort",
    "search",
    "random",
    "seed",
    "stable",
    "unsafe",
    "bound",
    "loop",
    "branch",
    "predict",
    "optimize",
    "profile",
    "trace",
    "heap",
    "stackframe",
    "allocator",
    "system",
    "process",
    "signal",
    "future",
    "async",
    "await",
    "channel",
    "actor",
    "mutex",
]


def gen_numbers(path: Path, count: int, seed: int) -> None:
    rnd = random.Random(seed)
    with path.open("w", encoding="utf-8") as f:
        for _ in range(count):
            f.write(f"{rnd.randint(0, 999999)}\n")


def gen_strings(path: Path, lines: int, seed: int) -> None:
    rnd = random.Random(seed + 1)
    with path.open("w", encoding="utf-8") as f:
        for _ in range(lines):
            words = [rnd.choice(VOCAB) for _ in range(rnd.randint(6, 18))]
            f.write(" ".join(words) + "\n")


def gen_primes(path: Path, limit: int) -> None:
    path.write_text(f"{limit}\n", encoding="utf-8")


def gen_life(path: Path, rows: int, cols: int, steps: int, seed: int) -> None:
    rnd = random.Random(seed + 2)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{rows} {cols} {steps}\n")
        for _ in range(rows):
            row = "".join("1" if rnd.random() < 0.35 else "0" for _ in range(cols))
            f.write(row + "\n")


def gen_io(path: Path, size_mb: int, seed: int) -> None:
    rnd = random.Random(seed + 3)
    size = size_mb * 1024 * 1024
    chunk = bytearray(1024 * 1024)
    with path.open("wb") as f:
        written = 0
        while written < size:
            to_write = min(len(chunk), size - written)
            for i in range(to_write):
                chunk[i] = rnd.randint(0, 255)
            f.write(chunk[:to_write])
            written += to_write


def gen_matmul(path: Path, size: int, seed_a: int, seed_b: int, value_mod: int) -> None:
    path.write_text(f"{size} {seed_a} {seed_b} {value_mod}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic benchmark inputs"
    )
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--numbers-count", type=int, default=20000)
    parser.add_argument("--strings-lines", type=int, default=22000)
    parser.add_argument("--primes-limit", type=int, default=175000000)
    parser.add_argument("--life-rows", type=int, default=256)
    parser.add_argument("--life-cols", type=int, default=256)
    parser.add_argument("--life-steps", type=int, default=220)
    parser.add_argument("--io-size-mb", type=int, default=32)
    parser.add_argument("--matmul-size", type=int, default=1024)
    parser.add_argument("--matmul-seed-a", type=int, default=12345)
    parser.add_argument("--matmul-seed-b", type=int, default=67890)
    parser.add_argument("--matmul-value-mod", type=int, default=97)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gen_numbers(out_dir / "numbers.txt", args.numbers_count, args.seed)
    gen_strings(out_dir / "strings.txt", args.strings_lines, args.seed)
    gen_primes(out_dir / "primes.txt", args.primes_limit)
    gen_life(
        out_dir / "life.txt", args.life_rows, args.life_cols, args.life_steps, args.seed
    )
    gen_io(out_dir / "io.bin", args.io_size_mb, args.seed)
    gen_matmul(
        out_dir / "matmul.txt",
        args.matmul_size,
        args.matmul_seed_a,
        args.matmul_seed_b,
        args.matmul_value_mod,
    )

    print(f"Generated inputs in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
