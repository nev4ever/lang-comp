#!/usr/bin/env python3
import argparse
import queue
import re
import threading
import time
from pathlib import Path

import numpy as np

MOD = 1_000_000_007


def checksum_numbers(values: np.ndarray) -> int:
    return int(values.sum(dtype=np.int64))


def has_inversion(values: np.ndarray) -> bool:
    if values.shape[0] < 2:
        return False
    return bool(np.any(values[1:] < values[:-1]))


def word_hash(word: str) -> int:
    h = 0
    for ch in word:
        h = (h * 131 + ord(ch)) % MOD
    return h


def checksum_strings(lines: list[str]) -> int:
    freq: dict[str, int] = {}
    for line in lines:
        for token in re.findall(r"[a-z0-9]+", line.lower()):
            freq[token] = freq.get(token, 0) + 1
    checksum = 0
    for token in sorted(freq.keys()):
        checksum = (checksum + (word_hash(token) * freq[token]) % MOD) % MOD
    return checksum


def sum_primes_numpy(limit: int) -> int:
    if limit < 2:
        return 0
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[:2] = False
    max_p = int(limit**0.5)
    for p in range(2, max_p + 1):
        if sieve[p]:
            sieve[p * p :: p] = False
    return int(np.nonzero(sieve)[0].sum(dtype=np.int64))


def parse_life(path: Path) -> tuple[np.ndarray, int]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows_s, cols_s, steps_s = lines[0].split()
    rows = int(rows_s)
    cols = int(cols_s)
    steps = int(steps_s)
    grid = np.zeros((rows, cols), dtype=np.uint8)
    for r in range(rows):
        row = lines[r + 1][:cols]
        grid[r] = np.fromiter((1 if ch == "1" else 0 for ch in row), dtype=np.uint8, count=cols)
    return grid, steps


def life_step(grid: np.ndarray) -> np.ndarray:
    neighbors = (
        np.roll(np.roll(grid, 1, 0), 1, 1)
        + np.roll(np.roll(grid, 1, 0), 0, 1)
        + np.roll(np.roll(grid, 1, 0), -1, 1)
        + np.roll(np.roll(grid, 0, 0), 1, 1)
        + np.roll(np.roll(grid, 0, 0), -1, 1)
        + np.roll(np.roll(grid, -1, 0), 1, 1)
        + np.roll(np.roll(grid, -1, 0), 0, 1)
        + np.roll(np.roll(grid, -1, 0), -1, 1)
    )
    # clear wrapped edges to match non-wrapping semantics
    neighbors[0, :] -= grid[-1, :] + np.roll(grid[-1, :], 1) + np.roll(grid[-1, :], -1)
    neighbors[-1, :] -= grid[0, :] + np.roll(grid[0, :], 1) + np.roll(grid[0, :], -1)
    neighbors[:, 0] -= grid[:, -1] + np.roll(grid[:, -1], 1) + np.roll(grid[:, -1], -1)
    neighbors[:, -1] -= grid[:, 0] + np.roll(grid[:, 0], 1) + np.roll(grid[:, 0], -1)
    survive = (grid == 1) & ((neighbors == 2) | (neighbors == 3))
    born = (grid == 0) & (neighbors == 3)
    return (survive | born).astype(np.uint8)


def game_of_life_checksum_numpy(base_grid: np.ndarray, steps: int) -> int:
    grid = base_grid.copy()
    for _ in range(steps):
        grid = life_step(grid)
    rows, cols = grid.shape
    idx = np.arange(rows * cols, dtype=np.int64).reshape(rows, cols) + 1
    return int((idx * grid).sum(dtype=np.int64))


def checksum_bytes_numpy(data: bytes) -> int:
    h = 0
    for b in data:
        h = (h * 257 + b) % MOD
    return h


def lcg32(x: int) -> int:
    return (1664525 * x + 1013904223) & 0xFFFFFFFF


def alloc_gc_checksum_numpy(objects: int, rounds: int, payload_words: int, seed: int) -> int:
    checksum = 0
    for r in range(rounds):
        base = (seed + r * 2654435761) & 0xFFFFFFFF
        items: list[tuple[int, int, int, int, int]] = []
        for i in range(objects):
            x = lcg32((base + i) & 0xFFFFFFFF)
            first = 0
            last = 0
            for p in range(payload_words):
                x = lcg32(x ^ ((p + 1) * 2246822519 & 0xFFFFFFFF))
                v = x % 9973
                if p == 0:
                    first = v
                last = v
            items.append((i, x % 1000003, (x >> 8) % 1000003, first, last))
        for item in items:
            checksum = (checksum + item[0] * 17 + item[1] * 31 + item[2] * 47 + item[3] * 73 + item[4] * 89) % MOD
    return checksum


def channel_queue_checksum(messages: int, queue_size: int, seed: int, threads: int) -> int:
    q: queue.Queue[int | None] = queue.Queue(maxsize=queue_size)
    producer_count = threads
    consumer_count = threads
    sums = [0] * consumer_count

    def producer(start: int, end: int) -> None:
        for i in range(start, end):
            x = lcg32((seed + i) & 0xFFFFFFFF)
            q.put(x % MOD)

    def consumer(idx: int) -> None:
        local = 0
        while True:
            value = q.get()
            if value is None:
                q.task_done()
                break
            local = (local + value) % MOD
            q.task_done()
        sums[idx] = local

    consumers = [threading.Thread(target=consumer, args=(i,)) for i in range(consumer_count)]
    for t in consumers:
        t.start()

    producers = []
    for p in range(producer_count):
        start = (p * messages) // producer_count
        end = ((p + 1) * messages) // producer_count
        t = threading.Thread(target=producer, args=(start, end))
        producers.append(t)
        t.start()

    for t in producers:
        t.join()
    for _ in range(consumer_count):
        q.put(None)
    for t in consumers:
        t.join()
    return sum(sums) % MOD


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError("runs must be >= 1")
    if args.threads < 1:
        raise ValueError("threads must be >= 1")

    path = Path(args.input)
    workload = args.workload
    n_value = 0

    if workload in {"quick", "merge"}:
        base_values = np.loadtxt(path, dtype=np.int64)
        n_value = int(base_values.shape[0])
    elif workload == "strings":
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        n_value = len(lines)
    elif workload == "primes":
        limit = int(next(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()))
        n_value = limit
    elif workload == "life":
        base_grid, steps = parse_life(path)
        n_value = int(base_grid.size)
    elif workload == "io":
        io_data = path.read_bytes()
        n_value = len(io_data)
    elif workload == "bubble":
        raise ValueError("python-numpy does not support workload: bubble")
    elif workload == "alloc_gc":
        alloc_objects, alloc_rounds, alloc_payload_words, alloc_seed = [
            int(x) for x in next(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()).split()
        ]
        n_value = alloc_objects
    elif workload == "channel_queue_mt":
        channel_messages, channel_queue_size, channel_seed = [
            int(x) for x in next(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()).split()
        ]
        n_value = channel_messages
    elif workload == "matmul_mt":
        raise ValueError("python-numpy target does not support workload: matmul_mt")
    else:
        raise ValueError(f"unknown workload: {workload}")

    run_times: list[float] = []
    checksum = 0
    for _ in range(args.runs):
        if workload == "quick":
            if not has_inversion(base_values):
                raise ValueError("sort input is already sorted before run")
            values = np.array(base_values, copy=True)
            start = time.perf_counter()
            values.sort(kind="quicksort")
            run_times.append((time.perf_counter() - start) * 1000)
            checksum = checksum_numbers(values)
        elif workload == "merge":
            if not has_inversion(base_values):
                raise ValueError("sort input is already sorted before run")
            values = np.array(base_values, copy=True)
            start = time.perf_counter()
            values.sort(kind="mergesort")
            run_times.append((time.perf_counter() - start) * 1000)
            checksum = checksum_numbers(values)
        elif workload == "strings":
            start = time.perf_counter()
            checksum = checksum_strings(lines)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "primes":
            start = time.perf_counter()
            checksum = sum_primes_numpy(limit)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "life":
            start = time.perf_counter()
            checksum = game_of_life_checksum_numpy(base_grid, steps)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "io":
            start = time.perf_counter()
            checksum = checksum_bytes_numpy(io_data)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "alloc_gc":
            start = time.perf_counter()
            checksum = alloc_gc_checksum_numpy(alloc_objects, alloc_rounds, alloc_payload_words, alloc_seed)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "channel_queue_mt":
            start = time.perf_counter()
            checksum = channel_queue_checksum(channel_messages, channel_queue_size, channel_seed, args.threads)
            run_times.append((time.perf_counter() - start) * 1000)

    slowest = max(run_times)
    if args.runs > 1:
        total = sum(run_times) - slowest
        effective_runs = args.runs - 1
    else:
        total = run_times[0]
        effective_runs = 1
    elapsed = total / effective_runs

    print(
        f"LANG=python-numpy WORKLOAD={workload} N={n_value} RUNS={args.runs} "
        f"THREADS={args.threads} EFFECTIVE_RUNS={effective_runs} ELAPSED_MS={elapsed:.3f} "
        f"TOTAL_ELAPSED_MS={total:.3f} SLOWEST_MS={slowest:.3f} CHECKSUM={checksum}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
