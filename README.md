# lang-comp

Cross-language benchmark suite with multiple workloads.

## Workloads

- `bubble` (sorting)
- `quick` (sorting)
- `merge` (sorting)
- `strings` (tokenization + frequency + hashing)
- `primes` (sieve sum)
- `life` (Conway's Game of Life simulation)
- `io` (read + byte checksum over a deterministic binary payload)
- `matmul_mt` (threaded matrix multiplication with deterministic generated matrices)
- `alloc_gc` (allocation/object churn with deterministic checksum)
- `channel_queue_mt` (threaded message-partition checksum workload)

## Workload Details

### `bubble`
- Goal: stress branch-heavy `O(n^2)` sorting loops.
- Input: `data/numbers.txt` (deterministic random integers).
- Implementation: in-place bubble sort; each run copies base input first.
- Notes: useful as a worst-case CPU loop benchmark, not a practical sorting baseline.

### `quick`
- Goal: compare fast comparison sorting paths.
- Input: `data/numbers.txt`.
- Implementation:
  - C/Go/Java/JS/Python: handwritten quicksort.
  - `python-numpy`: NumPy quicksort (`values.sort(kind=\"quicksort\")`).
- Notes: algorithm family is similar, but `python-numpy` uses native library code.

### `merge`
- Goal: compare stable divide-and-conquer sorting.
- Input: `data/numbers.txt`.
- Implementation:
  - C/Go/Java/JS/Python: merge sort implementation.
  - `python-numpy`: NumPy mergesort (`values.sort(kind=\"mergesort\")`).

### `strings`
- Goal: text processing / parser-like workload.
- Input: `data/strings.txt` (deterministic synthetic sentences).
- Implementation: lowercase tokenization via regex, token frequency map, deterministic hash reduction.
- Notes: captures regex + map + string handling overhead.

### `primes`
- Goal: integer-heavy compute benchmark.
- Input: `data/primes.txt` (single limit value).
- Implementation: sieve of Eratosthenes + sum of discovered primes.

### `life`
- Goal: grid simulation and memory access benchmark.
- Input: `data/life.txt` (rows/cols/steps + deterministic initial grid).
- Implementation: non-wrapping Conway Game of Life for configured steps, then deterministic grid checksum.
- Notes: sensitive to data layout and cache behavior.

### `io`
- Goal: streaming byte-processing benchmark.
- Input: `data/io.bin` (deterministic binary payload).
- Implementation: read file and compute rolling checksum `h = (h * 257 + byte) % MOD`.

### `matmul_mt`
- Goal: threaded numeric kernel benchmark.
- Input: `data/matmul.txt` (`N seedA seedB valueMod`).
- Implementation:
  - Generates matrices via deterministic LCG seeds.
  - Row-partitioned multi-thread matrix multiplication.
  - Thread count controlled by `--threads`.
- Supported targets: `node`, `c`, `go`, `java`.

### `alloc_gc`
- Goal: allocation pressure / object churn benchmark.
- Input: `data/alloc_gc.txt` (`objects rounds payloadWords seed`).
- Implementation:
  - Creates many short-lived object records with deterministic pseudo-random fields.
  - Reduces object data to checksum after each round.
- Notes: highlights allocator/GC/runtime overhead and object model cost.

### `channel_queue_mt`
- Goal: concurrent partition/reduction benchmark.
- Input: `data/channel_queue_mt.txt` (`messages queueSize seed`).
- Implementation:
  - Deterministic message value generation from index + seed.
  - Thread-partitioned local reductions, then final checksum combine.
  - Thread count controlled by `--threads`.
- Notes: compares concurrency scheduling and synchronization overhead.

All targets expose a unified CLI:

```bash
--workload <name> --input <file> --runs <n> --threads <n>
```

Each target reports:

- `ELAPSED_MS` (average over effective runs)
- `TOTAL_ELAPSED_MS` (sum over effective runs)
- `SLOWEST_MS` (dropped when `runs > 1`)
- `CHECKSUM` (cross-language correctness validation)

## Targets

- JavaScript (`node`, `bun`, `deno`)
- Python
- Python + NumPy (`python-numpy`, auto-skipped if NumPy is missing)
- C
- Go
- Java
- C# (.NET)
- Rust
- Zig

## Frameworks And Libraries

- Core workloads (`bubble`, `quick`, `merge`, `strings`, `primes`, `life`, `io`, `matmul_mt`, `alloc_gc`, `channel_queue_mt`) use standard libraries plus runtime-native facilities.
- `python-numpy` target uses NumPy for supported numeric workloads (`quick`, `merge`, `primes`, `life`).
- `zig` target currently uses the shared C benchmark implementation compiled via `zig cc` (toolchain comparison path).

## Arch Linux setup

```bash
sudo pacman -S --needed nodejs deno bun python go rust zig jdk-openjdk dotnet-sdk gcc make
```

## Dependency Installation

Install JavaScript deps (pipeline frameworks/ORMs):

```bash
cd /home/nev/dev/lang-comp
npm install
```

Install Python deps in a local virtualenv (recommended):

```bash
cd /home/nev/dev/lang-comp
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Or use Make targets:

```bash
make deps-js
make deps-py
make deps
```

## Usage

Generate deterministic input data:

```bash
make generate
# if using venv Python:
make PYTHON=.venv/bin/python generate
```

Build native/JVM targets:

```bash
make build
```

Run full benchmark suite:

```bash
make bench
# if using venv Python:
make PYTHON=.venv/bin/python bench
```

Run one workload only:

```bash
make bench-workload WORKLOAD=bubble
make bench-workload WORKLOAD=primes
make bench-workload WORKLOAD=matmul_mt THREADS=8
make bench-workload WORKLOAD=alloc_gc
make bench-workload WORKLOAD=channel_queue_mt THREADS=8
```

Direct harness examples:

```bash
python3 scripts/benchmark.py --runs 7 --warmup 0
python3 scripts/benchmark.py --workloads quick merge --targets c go java
python3 scripts/benchmark.py --workloads matmul_mt --threads 8
```

Pipeline benchmark (HTTP + JSON + DB roundtrip):

```bash
make bench-pipeline REQUESTS=300
python3 scripts/pipeline_benchmark.py --requests 500
python3 scripts/pipeline_benchmark.py --requests 2000 --request-timeout 10
# if using venv Python:
make PYTHON=.venv/bin/python bench-pipeline REQUESTS=300
```

Start/stop local PostgreSQL for ORM pipeline variants:

```bash
make pg-up
make pg-logs
make pg-down
```

Default mapped Postgres port for this benchmark compose file is `55432` (to avoid conflicts with local `5432`).

Run pipeline benchmark with explicit PostgreSQL DSN:

```bash
make bench-pipeline-pg REQUESTS=500
python3 scripts/pipeline_benchmark.py --db-backend postgres --requests 500 --pg-url postgresql://postgres:postgres@127.0.0.1:55432/langcomp
```

Generate a full CSV + ranking report (core + pipeline sqlite + pipeline postgres):

```bash
make bench-report
make bench-report REQUESTS=500 RUNS=5 THREADS=8
python3 scripts/benchmark_report.py --out-dir reports
```

Report outputs:
- `reports/benchmark_results.csv`: all per-scenario rows (`scenario`, `target`, `rank`, `elapsed_ms`).
- `reports/overall_language_ranking.csv`: language leaderboard using best rank per language in each scenario, then summed (lowest total rank wins).
- `reports/bar_*.txt`: ASCII bar charts for each scenario.
- `reports/bar_overall_rank_sum.txt`: ASCII bar chart for total rank-sum comparison.

### Pipeline Variants

- SQLite backend (`make bench-pipeline`):
  - `node-express-sql`: Node + Express + plain SQL.
  - `node-plain-sql`: Node built-in HTTP + plain SQL.
  - `deno-oak-sql`: Deno + Oak + plain SQL.
  - `bun-builtin-sql`: Bun built-in HTTP server + plain SQL.
  - `python-http-sql`: Python FastAPI + Uvicorn + plain SQL.
  - `go-http-sql`: Go `net/http` + plain SQL.
  - `java-http-sql`: Java `HttpServer` + plain SQL.
- Postgres backend (`make bench-pipeline-pg`):
  - `node-express-sequelize`: Node + Express + Sequelize ORM + PostgreSQL join query.
  - `node-express-drizzle`: Node + Express + Drizzle ORM + PostgreSQL `select().from().innerJoin()`.
  - `node-express-sql-pg`: Node + Express + plain SQL on PostgreSQL.
  - `node-plain-sql-pg`: Node built-in HTTP + plain SQL on PostgreSQL.
  - `bun-builtin-sql-pg`: Bun built-in HTTP + plain SQL on PostgreSQL.
  - `bun-builtin-drizzle`: Bun built-in HTTP + Drizzle ORM on PostgreSQL.

Pipeline implementation notes:
- Flow: HTTP request -> JSON parse -> deterministic business calc -> DB insert/select -> JSON response.
- Sequelize and Drizzle modes always use real ORM calls (not raw SQL path).
- Postgres pipeline run uses only Postgres-backed variants (all requests in that run hit Postgres).
- SQLite pipeline run uses SQLite-backed SQL variants.
- Framework-dependent variants skip gracefully if dependencies are not installed.

### Deno Oak Setup

If `deno-oak-sql` is skipped due to missing Oak in a Node-modules-managed workspace:

```bash
cat > deno.json <<'JSON'
{
  "nodeModulesDir": "auto",
  "imports": {
    "@oak/oak": "jsr:@oak/oak"
  }
}
JSON

deno install
deno cache --allow-import jsr:@oak/oak
```

## Notes

- Input generation is deterministic (`scripts/generate_data.py`, default seed `42`).
- For `runs > 1`, each target drops the slowest internal run to reduce outlier impact.
- Harness validates checksum equality per workload across all participating targets.
- `matmul_mt` is currently supported by `node`, `c`, `go`, and `java` in the harness.
- Pipeline variants skip gracefully if runtime/framework dependencies are unavailable.
