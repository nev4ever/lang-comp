#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

WORKLOADS = {
    "bubble": {"input": DATA_DIR / "numbers.txt"},
    "quick": {"input": DATA_DIR / "numbers.txt"},
    "merge": {"input": DATA_DIR / "numbers.txt"},
    "strings": {"input": DATA_DIR / "strings.txt"},
    "primes": {"input": DATA_DIR / "primes.txt"},
    "life": {"input": DATA_DIR / "life.txt"},
    "io": {"input": DATA_DIR / "io.bin"},
    "matmul_mt": {"input": DATA_DIR / "matmul.txt"},
}

TARGETS = {
    "node": {
        "cmd": ["node", str(ROOT / "targets" / "js" / "benchmark_node_bun.mjs")],
        "requires": ["node"],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io", "matmul_mt"],
    },
    "bun": {
        "cmd": ["bun", str(ROOT / "targets" / "js" / "benchmark_node_bun.mjs")],
        "requires": ["bun"],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io"],
    },
    "deno": {
        "cmd": [
            "deno",
            "run",
            "--allow-read",
            str(ROOT / "targets" / "js" / "benchmark_deno.js"),
        ],
        "requires": ["deno"],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io"],
    },
    "python": {
        "cmd": ["python3", str(ROOT / "targets" / "python" / "benchmark.py")],
        "requires": ["python3"],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io"],
    },
    "python-numpy": {
        "cmd": ["python3", str(ROOT / "targets" / "python" / "benchmark_numpy.py")],
        "requires": ["python3"],
        "python_modules": ["numpy"],
        "workloads": ["quick", "merge", "strings", "primes", "life", "io"],
    },
    "c": {
        "cmd": [str(ROOT / "bin" / "benchmark_c")],
        "requires": [],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io", "matmul_mt"],
    },
    "go": {
        "cmd": [str(ROOT / "bin" / "benchmark_go")],
        "requires": [],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io", "matmul_mt"],
    },
    "java": {
        "cmd": ["java", "-cp", str(ROOT / "bin" / "java"), "Benchmark"],
        "requires": ["java"],
        "workloads": ["bubble", "quick", "merge", "strings", "primes", "life", "io", "matmul_mt"],
    },
}

BUILD_TOOLS_BY_TARGET = {
    "c": ["gcc"],
    "go": ["go"],
    "java": ["javac", "java"],
}

CHECKSUM_RE = re.compile(r"CHECKSUM=(\d+)")
ELAPSED_RE = re.compile(r"ELAPSED_MS=([0-9]+(?:\.[0-9]+)?)")


def has_all_tools(tools: list[str]) -> bool:
    return all(shutil.which(t) is not None for t in tools)


def has_python_modules(python_exec: str, modules: list[str]) -> bool:
    if not modules:
        return True
    cmd = [python_exec, "-c", "import " + ",".join(modules)]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return proc.returncode == 0


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_built(selected_targets: list[str], strict: bool) -> list[str]:
    (ROOT / "bin").mkdir(exist_ok=True)
    (ROOT / "bin" / "java").mkdir(parents=True, exist_ok=True)

    available = []
    for target in selected_targets:
        tools = BUILD_TOOLS_BY_TARGET.get(target, [])
        if tools and not has_all_tools(tools):
            msg = f"Skipping {target}: missing build tools {', '.join(tools)}"
            if strict:
                raise RuntimeError(msg)
            print(msg)
            continue

        if target == "c":
            run([
                "gcc",
                "-O2",
                "-o",
                str(ROOT / "bin" / "benchmark_c"),
                str(ROOT / "targets" / "c" / "benchmark.c"),
            ])
        elif target == "go":
            run([
                "go",
                "build",
                "-o",
                str(ROOT / "bin" / "benchmark_go"),
                str(ROOT / "targets" / "go" / "benchmark.go"),
            ])
        elif target == "java":
            run([
                "javac",
                "-d",
                str(ROOT / "bin" / "java"),
                str(ROOT / "targets" / "java" / "Benchmark.java"),
            ])

        available.append(target)

    return available


def parse_elapsed_ms(output: str) -> float:
    m = ELAPSED_RE.search(output)
    if not m:
        raise ValueError(f"Missing ELAPSED_MS in output: {output}")
    return float(m.group(1))


def parse_checksum(output: str) -> str:
    m = CHECKSUM_RE.search(output)
    if not m:
        raise ValueError(f"Missing CHECKSUM in output: {output}")
    return m.group(1)


def run_target(target: str, workload: str, runs: int, threads: int) -> tuple[float, str]:
    input_file = WORKLOADS[workload]["input"]
    cmd = [
        *TARGETS[target]["cmd"],
        "--workload",
        workload,
        "--input",
        str(input_file),
        "--runs",
        str(runs),
        "--threads",
        str(threads),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        )
    output = proc.stdout.strip()
    return parse_elapsed_ms(output), output


def filter_runtime_available(selected_targets: list[str], strict: bool) -> list[str]:
    available = []
    for target in selected_targets:
        tools = TARGETS[target]["requires"]
        if tools and not has_all_tools(tools):
            msg = f"Skipping {target}: missing runtime tools {', '.join(tools)}"
            if strict:
                raise RuntimeError(msg)
            print(msg)
            continue
        py_modules = TARGETS[target].get("python_modules", [])
        if py_modules and not has_python_modules("python3", py_modules):
            msg = f"Skipping {target}: missing python modules {', '.join(py_modules)}"
            if strict:
                raise RuntimeError(msg)
            print(msg)
            continue
        available.append(target)
    return available


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark multiple workloads across languages/runtimes")
    parser.add_argument("--runs", type=int, default=5, help="Internal runs per target process")
    parser.add_argument("--warmup", type=int, default=0, help="Warmup executions per target/workload")
    parser.add_argument("--threads", type=int, default=4, help="Thread count for threaded workloads")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--targets", nargs="*", choices=list(TARGETS.keys()), help="Run only selected targets")
    parser.add_argument("--workloads", nargs="*", choices=list(WORKLOADS.keys()), help="Run only selected workloads")
    args = parser.parse_args()

    if args.runs < 1:
        print("--runs must be >= 1", file=sys.stderr)
        return 1
    if args.threads < 1:
        print("--threads must be >= 1", file=sys.stderr)
        return 1

    selected_targets = args.targets if args.targets else list(TARGETS.keys())
    selected_workloads = args.workloads if args.workloads else list(WORKLOADS.keys())

    strict_targets = bool(args.targets)
    selected_targets = filter_runtime_available(selected_targets, strict_targets)

    if not args.skip_build:
        selected_targets = ensure_built(selected_targets, strict_targets)

    if not selected_targets:
        print("No runnable targets.")
        return 1

    for workload in selected_workloads:
        input_file = WORKLOADS[workload]["input"]
        if not input_file.exists():
            print(f"Missing input file for workload '{workload}': {input_file}", file=sys.stderr)
            return 1

    print(f"Targets: {', '.join(selected_targets)}")
    print(f"Workloads: {', '.join(selected_workloads)}")
    print(f"Runs per process: {args.runs}, Warmups: {args.warmup}, Threads: {args.threads}\n")

    for workload in selected_workloads:
        print(f"== Workload: {workload} ==")
        baseline_checksum = None
        results: list[tuple[str, float, str]] = []
        workload_targets = [t for t in selected_targets if workload in TARGETS[t].get("workloads", WORKLOADS.keys())]
        skipped_for_workload = [t for t in selected_targets if t not in workload_targets]

        for target in skipped_for_workload:
            print(f"Skipping {target}: workload '{workload}' not supported")

        if not workload_targets:
            print("No runnable targets for this workload.\n")
            continue

        for target in workload_targets:
            for _ in range(args.warmup):
                _, warm_output = run_target(target, workload, args.runs, args.threads)
                warm_checksum = parse_checksum(warm_output)
                if baseline_checksum is None:
                    baseline_checksum = warm_checksum
                elif baseline_checksum != warm_checksum:
                    raise RuntimeError(
                        f"Checksum mismatch in warmup [{workload}] {target}: {warm_checksum} != {baseline_checksum}",
                    )

            elapsed, output = run_target(target, workload, args.runs, args.threads)
            checksum = parse_checksum(output)
            if baseline_checksum is None:
                baseline_checksum = checksum
            elif baseline_checksum != checksum:
                raise RuntimeError(
                    f"Checksum mismatch [{workload}] {target}: {checksum} != {baseline_checksum}",
                )
            results.append((target, elapsed, output))

        results.sort(key=lambda x: x[1])
        for rank, (target, elapsed, output) in enumerate(results, 1):
            print(f"{rank:>2}. {target:<7} {elapsed:>10.3f} ms")
            print(f"    {output}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
