#!/usr/bin/env python3
import argparse
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "numbers.txt"

TARGETS = {
    "node": {
        "cmd": ["node", str(ROOT / "js" / "node_bun_bubble_sort.mjs"), str(DATA_FILE)],
        "requires": ["node"],
    },
    "bun": {
        "cmd": ["bun", str(ROOT / "js" / "node_bun_bubble_sort.mjs"), str(DATA_FILE)],
        "requires": ["bun"],
    },
    "deno": {
        "cmd": ["deno", "run", "--allow-read", str(ROOT / "js" / "deno_bubble_sort.js"), str(DATA_FILE)],
        "requires": ["deno"],
    },
    "python": {
        "cmd": ["python3", str(ROOT / "python" / "bubble_sort.py"), str(DATA_FILE)],
        "requires": ["python3"],
    },
    "c": {
        "cmd": [str(ROOT / "bin" / "bubble_sort_c"), str(DATA_FILE)],
        "requires": [],
    },
    "go": {
        "cmd": [str(ROOT / "bin" / "bubble_sort_go"), str(DATA_FILE)],
        "requires": [],
    },
    "java": {
        "cmd": ["java", "-cp", str(ROOT / "bin" / "java"), "BubbleSort", str(DATA_FILE)],
        "requires": ["java"],
    },
}

BUILD_TOOLS_BY_TARGET = {
    "c": ["gcc"],
    "go": ["go"],
    "java": ["javac", "java"],
}

CHECKSUM_RE = re.compile(r"CHECKSUM=(\d+)")


def has_all_tools(tools: list[str]) -> bool:
    return all(shutil.which(t) is not None for t in tools)


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_built(selected: list[str], strict: bool) -> list[str]:
    (ROOT / "bin").mkdir(exist_ok=True)
    (ROOT / "bin" / "java").mkdir(parents=True, exist_ok=True)

    available = []
    for target in selected:
        tools = BUILD_TOOLS_BY_TARGET.get(target, [])
        if tools and not has_all_tools(tools):
            msg = f"Skipping {target}: missing build tools {', '.join(tools)}"
            if strict:
                raise RuntimeError(msg)
            print(msg)
            continue

        if target == "c":
            run(["gcc", "-O2", "-o", str(ROOT / "bin" / "bubble_sort_c"), str(ROOT / "c" / "bubble_sort.c")])
        elif target == "go":
            run(["go", "build", "-o", str(ROOT / "bin" / "bubble_sort_go"), str(ROOT / "go" / "bubble_sort.go")])
        elif target == "java":
            run(["javac", "-d", str(ROOT / "bin" / "java"), str(ROOT / "java" / "BubbleSort.java")])

        available.append(target)

    return available


def timed_run(cmd: list[str]) -> tuple[float, str]:
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return elapsed_ms, proc.stdout.strip()


def parse_checksum(line: str) -> str:
    m = CHECKSUM_RE.search(line)
    if not m:
        raise ValueError(f"Missing CHECKSUM in output: {line}")
    return m.group(1)


def filter_runtime_available(selected: list[str], strict: bool) -> list[str]:
    available = []
    for target in selected:
        tools = TARGETS[target]["requires"]
        if tools and not has_all_tools(tools):
            msg = f"Skipping {target}: missing runtime tools {', '.join(tools)}"
            if strict:
                raise RuntimeError(msg)
            print(msg)
            continue
        available.append(target)
    return available


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark bubble sort across languages/runtimes")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--only", nargs="*", choices=list(TARGETS.keys()), help="Run only selected targets")
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print(f"Missing {DATA_FILE}. Generate it first with data/generate_numbers.py", file=sys.stderr)
        return 1

    strict = bool(args.only)
    selected = args.only if args.only else list(TARGETS.keys())
    selected = filter_runtime_available(selected, strict)

    if not args.skip_build:
        selected = ensure_built(selected, strict)

    if not selected:
        print("No runnable targets. Install runtimes/compilers first.")
        return 1

    print(f"Benchmarking targets: {', '.join(selected)}")
    print(f"Input file: {DATA_FILE}")
    print(f"Warmups: {args.warmup}, Runs: {args.runs}\n")

    baseline_sum = None

    for name in selected:
        cmd = TARGETS[name]["cmd"]
        for _ in range(args.warmup):
            _, output = timed_run(cmd)
            csum = parse_checksum(output)
            if baseline_sum is None:
                baseline_sum = csum
            elif baseline_sum != csum:
                raise RuntimeError(f"Checksum mismatch during warmup for {name}: {csum} != {baseline_sum}")

        wall_times = []
        sample_output = ""
        for _ in range(args.runs):
            wall_ms, output = timed_run(cmd)
            csum = parse_checksum(output)
            if baseline_sum is None:
                baseline_sum = csum
            elif baseline_sum != csum:
                raise RuntimeError(f"Checksum mismatch for {name}: {csum} != {baseline_sum}")
            wall_times.append(wall_ms)
            sample_output = output

        mean_ms = statistics.mean(wall_times)
        median_ms = statistics.median(wall_times)
        min_ms = min(wall_times)
        max_ms = max(wall_times)
        print(f"[{name}] mean={mean_ms:.3f}ms median={median_ms:.3f}ms min={min_ms:.3f}ms max={max_ms:.3f}ms")
        print(f"  sample: {sample_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
