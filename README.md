# lang-comp

Cross-language bubble sort benchmark scaffold.

## Includes

- JavaScript on `node`, `deno`, `bun`
- Python
- C
- Go
- Java
- Shared numeric input file (`data/numbers.txt`) used by all implementations

## Arch Linux setup

Install required runtimes/compilers:

```bash
sudo pacman -S --needed nodejs deno bun python go jdk-openjdk gcc make
```

## Quick start

Generate deterministic random input (same file for all languages):

```bash
make generate
```

Run one implementation:

```bash
make run-python
make run-node
make run-deno
make run-bun
make run-c
make run-go
make run-java
```

Run all benchmarks:

```bash
make bench
```

Or call benchmark script directly:

```bash
python3 scripts/benchmark.py --runs 8 --warmup 2
python3 scripts/benchmark.py --only node bun deno
```

## Notes

- Each program times only the sort phase (file read/parse is outside timer).
- Benchmark script measures full process wall time and also validates `CHECKSUM` equality across targets.
- Current baseline algorithm is iterative bubble sort. You can add recursive variants/other sorts later while keeping the same input file and runner style.
