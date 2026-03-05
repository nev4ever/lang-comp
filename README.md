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

## Arch Linux setup

```bash
sudo pacman -S --needed nodejs deno bun python go jdk-openjdk gcc make
```

## Usage

Generate deterministic input data:

```bash
make generate
```

Build native/JVM targets:

```bash
make build
```

Run full benchmark suite:

```bash
make bench
```

Run one workload only:

```bash
make bench-workload WORKLOAD=bubble
make bench-workload WORKLOAD=primes
make bench-workload WORKLOAD=matmul_mt THREADS=8
```

Direct harness examples:

```bash
python3 scripts/benchmark.py --runs 7 --warmup 0
python3 scripts/benchmark.py --workloads quick merge --targets c go java
python3 scripts/benchmark.py --workloads matmul_mt --threads 8
```

## Notes

- Input generation is deterministic (`scripts/generate_data.py`, default seed `42`).
- For `runs > 1`, each target drops the slowest internal run to reduce outlier impact.
- Harness validates checksum equality per workload across all participating targets.
- `matmul_mt` is currently supported by `node`, `c`, `go`, and `java` in the harness.
