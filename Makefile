.PHONY: deps deps-js deps-py pg-up pg-down pg-logs generate build bench bench-workload bench-pipeline bench-pipeline-pg clean

PYTHON ?= python3

deps: deps-js deps-py

deps-js:
	npm install

deps-py:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

generate:
	$(PYTHON) scripts/generate_data.py --out-dir data

build:
	mkdir -p bin bin/java
	gcc -O3 -march=native -mtune=native -flto -pthread -o bin/benchmark_c targets/c/benchmark.c
	go build -o bin/benchmark_go targets/go/benchmark.go
	javac -d bin/java targets/java/Benchmark.java
	dotnet build targets/csharp/Benchmark.csproj -c Release -o bin/csharp
	@if command -v rustc >/dev/null 2>&1; then rustc -O targets/rust/main.rs -o bin/benchmark_rust; else echo "Skipping rust build: rustc not found"; fi
	@if command -v zig >/dev/null 2>&1; then zig cc -O3 -pthread -o bin/benchmark_zig targets/c/benchmark.c; else echo "Skipping zig build: zig not found"; fi

bench:
	$(PYTHON) scripts/benchmark.py --runs 5 --warmup 0 --threads 8

bench-workload:
	$(PYTHON) scripts/benchmark.py --runs 5 --warmup 0 --threads $(or $(THREADS),4) --workloads $(WORKLOAD)

bench-pipeline:
	$(PYTHON) scripts/pipeline_benchmark.py --db-backend sqlite --requests $(or $(REQUESTS),300)

bench-pipeline-pg: pg-up
	PIPELINE_PG_URL=$(or $(PG_URL),postgresql://postgres:postgres@127.0.0.1:55432/langcomp) \
	$(PYTHON) scripts/pipeline_benchmark.py --db-backend postgres --requests $(or $(REQUESTS),300)

pg-up:
	docker compose -f docker-compose.pipeline.yml up -d

pg-down:
	docker compose -f docker-compose.pipeline.yml down

pg-logs:
	docker compose -f docker-compose.pipeline.yml logs -f pipeline-postgres

clean:
	rm -rf bin
