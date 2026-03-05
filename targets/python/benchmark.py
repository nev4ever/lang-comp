#!/usr/bin/env python3
import argparse
import re
import time
from pathlib import Path

MOD = 1_000_000_007


def bubble_sort(values: list[int]) -> None:
    n = len(values)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if values[j] > values[j + 1]:
                values[j], values[j + 1] = values[j + 1], values[j]
                swapped = True
        if not swapped:
            break


def has_inversion(values: list[int]) -> bool:
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            return True
    return False


def quick_sort(values: list[int], low: int, high: int) -> None:
    if low >= high:
        return
    pivot = values[(low + high) // 2]
    i, j = low, high
    while i <= j:
        while values[i] < pivot:
            i += 1
        while values[j] > pivot:
            j -= 1
        if i <= j:
            values[i], values[j] = values[j], values[i]
            i += 1
            j -= 1
    if low < j:
        quick_sort(values, low, j)
    if i < high:
        quick_sort(values, i, high)


def merge_sort(values: list[int]) -> list[int]:
    if len(values) <= 1:
        return values
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    merged: list[int] = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    if i < len(left):
        merged.extend(left[i:])
    if j < len(right):
        merged.extend(right[j:])
    return merged


def checksum_numbers(values: list[int]) -> int:
    return sum(values)


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


def checksum_bytes(data: bytes) -> int:
    h = 0
    for b in data:
        h = (h * 257 + b) % MOD
    return h


def sum_primes(limit: int) -> int:
    if limit < 2:
        return 0
    sieve = [True] * (limit + 1)
    sieve[0] = False
    sieve[1] = False
    p = 2
    while p * p <= limit:
        if sieve[p]:
            start = p * p
            for i in range(start, limit + 1, p):
                sieve[i] = False
        p += 1
    total = 0
    for i, is_prime in enumerate(sieve):
        if is_prime:
            total += i
    return total


def parse_life(path: Path) -> tuple[list[list[int]], int]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    header = lines[0].split()
    rows, cols, steps = int(header[0]), int(header[1]), int(header[2])
    grid: list[list[int]] = []
    for r in range(rows):
        line = lines[r + 1]
        grid.append([1 if c == "1" else 0 for c in line[:cols]])
    return grid, steps


def game_of_life_checksum(base_grid: list[list[int]], steps: int) -> int:
    rows = len(base_grid)
    cols = len(base_grid[0]) if rows else 0
    grid = [row[:] for row in base_grid]
    next_grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for _ in range(steps):
        for r in range(rows):
            for c in range(cols):
                neighbors = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr = r + dr
                        nc = c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            neighbors += grid[nr][nc]
                if grid[r][c] == 1:
                    next_grid[r][c] = 1 if neighbors in (2, 3) else 0
                else:
                    next_grid[r][c] = 1 if neighbors == 3 else 0
        grid, next_grid = next_grid, grid
    checksum = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                checksum += r * cols + c + 1
    return checksum


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

    if workload in {"bubble", "quick", "merge"}:
        base_values = [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        n_value = len(base_values)
    elif workload == "strings":
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        n_value = len(lines)
    elif workload == "primes":
        limit = int(next(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()))
        n_value = limit
    elif workload == "life":
        base_grid, steps = parse_life(path)
        n_value = len(base_grid) * (len(base_grid[0]) if base_grid else 0)
    elif workload == "io":
        io_data = path.read_bytes()
        n_value = len(io_data)
    elif workload == "matmul_mt":
        raise ValueError("python target does not support workload: matmul_mt")
    else:
        raise ValueError(f"unknown workload: {workload}")

    run_times: list[float] = []
    checksum = 0
    for _ in range(args.runs):
        if workload == "bubble":
            if not has_inversion(base_values):
                raise ValueError("sort input is already sorted before run")
            values = base_values.copy()
            start = time.perf_counter()
            bubble_sort(values)
            run_times.append((time.perf_counter() - start) * 1000)
            checksum = checksum_numbers(values)
        elif workload == "quick":
            if not has_inversion(base_values):
                raise ValueError("sort input is already sorted before run")
            values = base_values.copy()
            start = time.perf_counter()
            quick_sort(values, 0, len(values) - 1)
            run_times.append((time.perf_counter() - start) * 1000)
            checksum = checksum_numbers(values)
        elif workload == "merge":
            if not has_inversion(base_values):
                raise ValueError("sort input is already sorted before run")
            values = base_values.copy()
            start = time.perf_counter()
            sorted_values = merge_sort(values)
            run_times.append((time.perf_counter() - start) * 1000)
            checksum = checksum_numbers(sorted_values)
        elif workload == "strings":
            start = time.perf_counter()
            checksum = checksum_strings(lines)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "primes":
            start = time.perf_counter()
            checksum = sum_primes(limit)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "life":
            start = time.perf_counter()
            checksum = game_of_life_checksum(base_grid, steps)
            run_times.append((time.perf_counter() - start) * 1000)
        elif workload == "io":
            start = time.perf_counter()
            checksum = checksum_bytes(io_data)
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
        f"LANG=python WORKLOAD={workload} N={n_value} RUNS={args.runs} "
        f"THREADS={args.threads} EFFECTIVE_RUNS={effective_runs} ELAPSED_MS={elapsed:.3f} "
        f"TOTAL_ELAPSED_MS={total:.3f} SLOWEST_MS={slowest:.3f} CHECKSUM={checksum}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
