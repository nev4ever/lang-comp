DATA_FILE=data/numbers.txt

.PHONY: generate build run-node run-bun run-deno run-python run-c run-go run-java bench clean

generate:
	python3 data/generate_numbers.py --count 2000 --seed 42 --output $(DATA_FILE)

build:
	mkdir -p bin bin/java
	gcc -O2 -o bin/bubble_sort_c c/bubble_sort.c
	go build -o bin/bubble_sort_go go/bubble_sort.go
	javac -d bin/java java/BubbleSort.java

run-node:
	node js/node_bun_bubble_sort.mjs $(DATA_FILE)

run-bun:
	bun js/node_bun_bubble_sort.mjs $(DATA_FILE)

run-deno:
	deno run --allow-read js/deno_bubble_sort.js $(DATA_FILE)

run-python:
	python3 python/bubble_sort.py $(DATA_FILE)

run-c: build
	./bin/bubble_sort_c $(DATA_FILE)

run-go: build
	./bin/bubble_sort_go $(DATA_FILE)

run-java: build
	java -cp bin/java BubbleSort $(DATA_FILE)

bench:
	python3 scripts/benchmark.py --runs 5 --warmup 1

clean:
	rm -rf bin
