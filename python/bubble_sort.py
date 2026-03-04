#!/usr/bin/env python3
import sys
import time
from pathlib import Path


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


def checksum(values: list[int]) -> int:
    return sum(values)


def read_numbers(path: Path) -> list[int]:
    return [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: bubble_sort.py <numbers_file>", file=sys.stderr)
        return 1

    values = read_numbers(Path(sys.argv[1]))
    start = time.perf_counter()
    bubble_sort(values)
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"LANG=python N={len(values)} ELAPSED_MS={elapsed_ms:.3f} CHECKSUM={checksum(values)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
