#!/usr/bin/env python3
import argparse
import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"

WORKLOAD_RE = re.compile(r"^== Workload: ([a-zA-Z0-9_]+) ==")
PIPELINE_BACKEND_RE = re.compile(r"^Pipeline backend: (sqlite|postgres)")
RESULT_LINE_RE = re.compile(r"^\s*(\d+)\.\s+([a-zA-Z0-9_-]+)\s+([0-9]+(?:\.[0-9]+)?)\s+ms\s*$")


def run_cmd(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc.stdout


def parse_core_output(text: str) -> list[dict[str, str | int | float]]:
    rows: list[dict[str, str | int | float]] = []
    workload = ""
    for line in text.splitlines():
        m_workload = WORKLOAD_RE.match(line.strip())
        if m_workload:
            workload = m_workload.group(1)
            continue
        m_result = RESULT_LINE_RE.match(line)
        if m_result and workload:
            rows.append(
                {
                    "suite": "core",
                    "backend": "",
                    "scenario": workload,
                    "rank": int(m_result.group(1)),
                    "target": m_result.group(2),
                    "language": infer_language(m_result.group(2)),
                    "elapsed_ms": float(m_result.group(3)),
                },
            )
    return rows


def parse_pipeline_output(text: str) -> list[dict[str, str | int | float]]:
    rows: list[dict[str, str | int | float]] = []
    backend = ""
    for line in text.splitlines():
        m_backend = PIPELINE_BACKEND_RE.match(line.strip())
        if m_backend:
            backend = m_backend.group(1)
            continue
        m_result = RESULT_LINE_RE.match(line)
        if m_result and backend:
            rows.append(
                {
                    "suite": "pipeline",
                    "backend": backend,
                    "scenario": f"pipeline_{backend}",
                    "rank": int(m_result.group(1)),
                    "target": m_result.group(2),
                    "language": infer_language(m_result.group(2)),
                    "elapsed_ms": float(m_result.group(3)),
                },
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["suite", "backend", "scenario", "rank", "target", "language", "elapsed_ms"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_table(headers: list[str], data_rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in data_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    sep = " | "
    print(sep.join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * w for w in widths))
    for row in data_rows:
        print(sep.join(row[i].ljust(widths[i]) for i in range(len(headers))))


def bar_chart_lines(
    title: str,
    labels_and_values: list[tuple[str, float]],
    width: int = 72,
    python_truncate_multiplier: float = 1.2,
) -> list[str]:
    lines = [title]
    if not labels_and_values:
        lines.append("(no data)")
        return lines

    non_python_values = [v for label, v in labels_and_values if not label.startswith("python")]
    non_python_max = max(non_python_values) if non_python_values else max(v for _, v in labels_and_values)
    python_cap = non_python_max * python_truncate_multiplier

    display_rows: list[tuple[str, float, float, bool]] = []
    for label, value in labels_and_values:
        truncated = False
        display_value = value
        if label.startswith("python") and value > python_cap:
            display_value = python_cap
            truncated = True
        display_rows.append((label, value, display_value, truncated))

    max_v = max(v for _, _, v, _ in display_rows)
    max_v = max(max_v, 1e-9)
    had_truncation = False
    for label, actual_value, display_value, truncated in display_rows:
        n = int(round((display_value / max_v) * width))
        bar = "#" * max(n, 1)
        suffix = " [truncated]" if truncated else ""
        if truncated:
            had_truncation = True
        lines.append(f"{label:<24} {actual_value:>10.3f} | {bar}{suffix}")
    if had_truncation:
        lines.append(f"(python bars truncated at {python_truncate_multiplier:.2f}x non-python max for readability)")
    return lines


def infer_language(target: str) -> str:
    if target.startswith("node"):
        return "node"
    if target.startswith("bun"):
        return "bun"
    if target.startswith("deno"):
        return "deno"
    if target.startswith("java"):
        return "java"
    if target.startswith("go"):
        return "go"
    if target.startswith("python"):
        return "python"
    if target.startswith("csharp"):
        return "csharp"
    if target.startswith("rust"):
        return "rust"
    if target.startswith("zig"):
        return "zig"
    if target == "c":
        return "c"
    return target


def build_overall_ranking(rows: list[dict[str, str | int | float]]) -> list[dict[str, str | int | float]]:
    best_by_scenario_language: dict[tuple[str, str], int] = {}
    for row in rows:
        scenario = str(row["scenario"])
        language = str(row["language"])
        rank = int(row["rank"])
        key = (scenario, language)
        if key not in best_by_scenario_language or rank < best_by_scenario_language[key]:
            best_by_scenario_language[key] = rank

    sums: dict[str, int] = defaultdict(int)
    counts: dict[str, int] = defaultdict(int)
    for (_, language), rank in best_by_scenario_language.items():
        sums[language] += rank
        counts[language] += 1

    ranking: list[dict[str, str | int | float]] = []
    for language, sum_rank in sums.items():
        cnt = counts[language]
        ranking.append(
            {
                "language": language,
                "sum_rank": sum_rank,
                "scenarios": cnt,
                "avg_rank": (sum_rank / cnt) if cnt else 0.0,
            },
        )
    ranking.sort(key=lambda r: (int(r["sum_rank"]), float(r["avg_rank"]), str(r["language"])))
    return ranking


def save_chart(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def maybe_start_pg(pg_enabled: bool) -> bool:
    if not pg_enabled:
        return False
    cmd = ["docker", "compose", "-f", str(ROOT / "docker-compose.pipeline.yml"), "up", "-d"]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        print("Skipping pipeline postgres benchmark: could not start postgres container.", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr.strip(), file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run benchmarks and generate CSV + ranking report")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=0)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--requests", type=int, default=300)
    parser.add_argument("--request-timeout", type=float, default=10.0)
    parser.add_argument("--pg-url", default="postgresql://postgres:postgres@127.0.0.1:55432/langcomp")
    parser.add_argument("--out-dir", default=str(REPORT_DIR))
    parser.add_argument("--skip-core", action="store_true")
    parser.add_argument("--skip-pipeline-sqlite", action="store_true")
    parser.add_argument("--skip-pipeline-pg", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    all_rows: list[dict[str, str | int | float]] = []

    if not args.skip_core:
        core_out = run_cmd(
            [
                "python3",
                str(ROOT / "scripts" / "benchmark.py"),
                "--runs",
                str(args.runs),
                "--warmup",
                str(args.warmup),
                "--threads",
                str(args.threads),
            ],
        )
        all_rows.extend(parse_core_output(core_out))

    if not args.skip_pipeline_sqlite:
        pipe_sqlite_out = run_cmd(
            [
                "python3",
                str(ROOT / "scripts" / "pipeline_benchmark.py"),
                "--db-backend",
                "sqlite",
                "--requests",
                str(args.requests),
                "--request-timeout",
                str(args.request_timeout),
            ],
        )
        all_rows.extend(parse_pipeline_output(pipe_sqlite_out))

    if not args.skip_pipeline_pg:
        if maybe_start_pg(True):
            pipe_pg_out = run_cmd(
                [
                    "python3",
                    str(ROOT / "scripts" / "pipeline_benchmark.py"),
                    "--db-backend",
                    "postgres",
                    "--requests",
                    str(args.requests),
                    "--request-timeout",
                    str(args.request_timeout),
                    "--pg-url",
                    str(args.pg_url),
                ],
            )
            all_rows.extend(parse_pipeline_output(pipe_pg_out))

    if not all_rows:
        print("No benchmark rows collected.", file=sys.stderr)
        return 1

    all_rows.sort(key=lambda r: (str(r["scenario"]), int(r["rank"]), str(r["target"])))
    write_csv(out_dir / "benchmark_results.csv", all_rows)

    scenario_groups: dict[str, list[dict[str, str | int | float]]] = defaultdict(list)
    for row in all_rows:
        scenario_groups[str(row["scenario"])].append(row)

    print("\n== Scenario Tables ==")
    for scenario in sorted(scenario_groups.keys()):
        rows = sorted(scenario_groups[scenario], key=lambda r: int(r["rank"]))
        table_rows = [
            [
                str(r["rank"]),
                str(r["target"]),
                str(r["language"]),
                f"{float(r['elapsed_ms']):.3f}",
                str(r["suite"]),
                str(r["backend"]),
            ]
            for r in rows
        ]
        print(f"\n[{scenario}]")
        print_table(["Rank", "Target", "Language", "ElapsedMs", "Suite", "Backend"], table_rows)

    overall = build_overall_ranking(all_rows)
    overall_rows = [
        [str(i + 1), str(r["language"]), str(r["sum_rank"]), str(r["scenarios"]), f"{float(r['avg_rank']):.3f}"]
        for i, r in enumerate(overall)
    ]
    print("\n== Overall Language Ranking (Lowest Rank Sum Wins) ==")
    print_table(["Pos", "Language", "RankSum", "Scenarios", "AvgRank"], overall_rows)

    with (out_dir / "overall_language_ranking.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["position", "language", "sum_rank", "scenarios", "avg_rank"])
        writer.writeheader()
        for i, r in enumerate(overall, start=1):
            writer.writerow(
                {
                    "position": i,
                    "language": r["language"],
                    "sum_rank": r["sum_rank"],
                    "scenarios": r["scenarios"],
                    "avg_rank": f"{float(r['avg_rank']):.6f}",
                },
            )

    print("\n== Bar Charts ==")
    for scenario in sorted(scenario_groups.keys()):
        rows = sorted(scenario_groups[scenario], key=lambda r: float(r["elapsed_ms"]))
        chart = bar_chart_lines(
            f"[{scenario}] elapsed ms (lower is better)",
            [(str(r["target"]), float(r["elapsed_ms"])) for r in rows],
        )
        print("\n" + "\n".join(chart))
        save_chart(out_dir / f"bar_{scenario}.txt", chart)

    rank_sum_chart = bar_chart_lines(
        "[overall] rank sum (lower is better)",
        [(str(r["language"]), float(r["sum_rank"])) for r in overall],
    )
    print("\n" + "\n".join(rank_sum_chart))
    save_chart(out_dir / "bar_overall_rank_sum.txt", rank_sum_chart)

    print(f"\nSaved: {out_dir / 'benchmark_results.csv'}")
    print(f"Saved: {out_dir / 'overall_language_ranking.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
