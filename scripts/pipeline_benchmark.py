#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = 1_000_000_007


def has_tools(tools: list[str]) -> bool:
    return all(shutil.which(t) is not None for t in tools)


def wait_for_health(port: int, timeout_s: float = 8.0) -> bool:
    deadline = time.time() + timeout_s
    url = f"http://127.0.0.1:{port}/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.05)
    return False


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_load(port: int, requests: int, request_timeout_s: float) -> tuple[float, int]:
    url = f"http://127.0.0.1:{port}/orders"
    checksum = 0
    start = time.perf_counter()
    for i in range(requests):
        payload = {
            "customerId": i % 1000,
            "itemCount": (i % 5) + 1,
            "baseCents": 125 + (i % 19),
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=request_timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            checksum = (checksum + (i + 1) * 31 + int(data.get("totalCents", 0)) * 17) % MOD
    elapsed_ms = (time.perf_counter() - start) * 1000
    return elapsed_ms, checksum


def run_variant(name: str, cmd: list[str], requests: int, request_timeout_s: float) -> tuple[bool, str]:
    if not has_tools([cmd[0]]):
        return False, f"Skipping {name}: missing runtime {cmd[0]}"

    with tempfile.TemporaryDirectory(prefix=f"pipeline_{name}_") as td:
        db_path = os.path.join(td, "pipeline.db")
        port = free_port()
        full_cmd = [*cmd, "--port", str(port), "--db", db_path]
        proc = subprocess.Popen(full_cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        try:
            time.sleep(0.2)
            if proc.poll() is not None:
                stderr = (proc.stderr.read() or "").strip()
                if "SKIP:" in stderr:
                    return False, f"Skipping {name}: {stderr.split('SKIP:', 1)[1].strip()}"
                return False, f"Skipping {name}: failed to start ({stderr or 'no stderr'})"

            if not wait_for_health(port):
                return False, f"Skipping {name}: health check failed"

            elapsed, checksum = run_load(port, requests, request_timeout_s)
            return True, f"{name}: ELAPSED_MS={elapsed:.3f} REQUESTS={requests} CHECKSUM={checksum}"
        except Exception as err:
            return False, f"Failed {name}: {err}"
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


def ensure_builds() -> None:
    (ROOT / "bin").mkdir(exist_ok=True)
    (ROOT / "bin" / "java").mkdir(parents=True, exist_ok=True)

    if has_tools(["go"]):
        subprocess.run(
            ["go", "build", "-o", str(ROOT / "bin" / "pipeline_go"), str(ROOT / "targets" / "pipeline" / "go_pipeline.go")],
            check=True,
            cwd=ROOT,
        )
    if has_tools(["javac"]):
        subprocess.run(
            ["javac", "-d", str(ROOT / "bin" / "java"), str(ROOT / "targets" / "pipeline" / "PipelineServer.java")],
            check=True,
            cwd=ROOT,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline benchmark (HTTP + JSON + DB)")
    parser.add_argument("--requests", type=int, default=300)
    parser.add_argument("--request-timeout", type=float, default=10.0)
    parser.add_argument("--db-backend", choices=["sqlite", "postgres"], default="sqlite")
    parser.add_argument(
        "--pg-url",
        default=os.environ.get("PIPELINE_PG_URL", "postgresql://postgres:postgres@127.0.0.1:55432/langcomp"),
        help="Postgres DSN for ORM pipeline variants",
    )
    args = parser.parse_args()

    ensure_builds()

    if args.db_backend == "postgres":
        variants: list[tuple[str, list[str]]] = [
            (
                "node-express-sequelize",
                [
                    "node",
                    str(ROOT / "targets" / "pipeline" / "node_pipeline.mjs"),
                    "--mode",
                    "express-sequelize",
                    "--db-backend",
                    "postgres",
                    "--pg-url",
                    args.pg_url,
                ],
            ),
            (
                "node-express-drizzle",
                [
                    "node",
                    str(ROOT / "targets" / "pipeline" / "node_pipeline.mjs"),
                    "--mode",
                    "express-drizzle",
                    "--db-backend",
                    "postgres",
                    "--pg-url",
                    args.pg_url,
                ],
            ),
            (
                "node-express-sql-pg",
                [
                    "node",
                    str(ROOT / "targets" / "pipeline" / "node_pipeline.mjs"),
                    "--mode",
                    "express-sql",
                    "--db-backend",
                    "postgres",
                    "--pg-url",
                    args.pg_url,
                ],
            ),
            (
                "node-plain-sql-pg",
                [
                    "node",
                    str(ROOT / "targets" / "pipeline" / "node_pipeline.mjs"),
                    "--mode",
                    "plain",
                    "--db-backend",
                    "postgres",
                    "--pg-url",
                    args.pg_url,
                ],
            ),
            (
                "bun-builtin-sql-pg",
                [
                    "bun",
                    str(ROOT / "targets" / "pipeline" / "bun_pipeline.js"),
                    "--mode",
                    "builtin-sql",
                    "--db-backend",
                    "postgres",
                    "--pg-url",
                    args.pg_url,
                ],
            ),
            (
                "bun-builtin-drizzle",
                [
                    "bun",
                    str(ROOT / "targets" / "pipeline" / "bun_pipeline.js"),
                    "--mode",
                    "builtin-drizzle",
                    "--db-backend",
                    "postgres",
                    "--pg-url",
                    args.pg_url,
                ],
            ),
        ]
    else:
        variants = [
            ("node-express-sql", ["node", str(ROOT / "targets" / "pipeline" / "node_pipeline.mjs"), "--mode", "express-sql", "--db-backend", "sqlite"]),
            ("node-plain-sql", ["node", str(ROOT / "targets" / "pipeline" / "node_pipeline.mjs"), "--mode", "plain", "--db-backend", "sqlite"]),
            ("deno-oak-sql", ["deno", "run", "--allow-net", "--allow-run", "--allow-read", str(ROOT / "targets" / "pipeline" / "deno_pipeline.js"), "--mode", "oak"]),
            ("bun-builtin-sql", ["bun", str(ROOT / "targets" / "pipeline" / "bun_pipeline.js"), "--mode", "builtin-sql", "--db-backend", "sqlite"]),
            ("python-http-sql", ["python3", str(ROOT / "targets" / "pipeline" / "python_pipeline.py")]),
            ("go-http-sql", [str(ROOT / "bin" / "pipeline_go")]),
            ("java-http-sql", ["java", "-cp", str(ROOT / "bin" / "java"), "PipelineServer"]),
        ]

    results: list[tuple[str, float, str]] = []
    print(f"Pipeline backend: {args.db_backend}")
    print(f"Pipeline requests: {args.requests}, per-request timeout: {args.request_timeout:.1f}s")
    if args.db_backend == "postgres":
        print(f"Postgres DSN: {args.pg_url}")

    for name, cmd in variants:
        ok, line = run_variant(name, cmd, args.requests, args.request_timeout)
        if ok:
            elapsed = float(line.split("ELAPSED_MS=")[1].split()[0])
            results.append((name, elapsed, line))
        else:
            print(line)

    results.sort(key=lambda x: x[1])
    for rank, (name, elapsed, line) in enumerate(results, 1):
        print(f"{rank:>2}. {name:<24} {elapsed:>10.3f} ms")
        print(f"    {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
