.PHONY: generate build bench bench-workload clean

generate:
	python3 scripts/generate_data.py --out-dir data

build:
	mkdir -p bin bin/java
	gcc -O3 -march=native -mtune=native -flto -pthread -o bin/benchmark_c targets/c/benchmark.c
	go build -o bin/benchmark_go targets/go/benchmark.go
	javac -d bin/java targets/java/Benchmark.java

bench:
	python3 scripts/benchmark.py --runs 5 --warmup 0 --threads 4

bench-workload:
	python3 scripts/benchmark.py --runs 5 --warmup 0 --threads $(or $(THREADS),4) --workloads $(WORKLOAD)

clean:
	rm -rf bin
