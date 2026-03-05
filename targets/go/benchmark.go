package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

const mod uint64 = 1_000_000_007

func bubbleSort(values []int) {
	n := len(values)
	for i := 0; i < n; i++ {
		swapped := false
		for j := 0; j < n-i-1; j++ {
			if values[j] > values[j+1] {
				values[j], values[j+1] = values[j+1], values[j]
				swapped = true
			}
		}
		if !swapped {
			return
		}
	}
}

func hasInversion(values []int) bool {
	for i := 1; i < len(values); i++ {
		if values[i] < values[i-1] {
			return true
		}
	}
	return false
}

func quickSort(values []int, low int, high int) {
	if low >= high {
		return
	}
	pivot := values[(low+high)/2]
	i := low
	j := high
	for i <= j {
		for values[i] < pivot {
			i++
		}
		for values[j] > pivot {
			j--
		}
		if i <= j {
			values[i], values[j] = values[j], values[i]
			i++
			j--
		}
	}
	if low < j {
		quickSort(values, low, j)
	}
	if i < high {
		quickSort(values, i, high)
	}
}

func mergeSort(values []int) []int {
	if len(values) <= 1 {
		return values
	}
	mid := len(values) / 2
	left := mergeSort(append([]int(nil), values[:mid]...))
	right := mergeSort(append([]int(nil), values[mid:]...))
	merged := make([]int, 0, len(values))
	i := 0
	j := 0
	for i < len(left) && j < len(right) {
		if left[i] <= right[j] {
			merged = append(merged, left[i])
			i++
		} else {
			merged = append(merged, right[j])
			j++
		}
	}
	merged = append(merged, left[i:]...)
	merged = append(merged, right[j:]...)
	return merged
}

func checksumNumbers(values []int) int64 {
	var sum int64
	for _, v := range values {
		sum += int64(v)
	}
	return sum
}

func wordHash(word string) uint64 {
	var h uint64
	for _, ch := range word {
		h = (h*131 + uint64(ch)) % mod
	}
	return h
}

var tokenRe = regexp.MustCompile(`[a-z0-9]+`)

func checksumStrings(lines []string) uint64 {
	freq := make(map[string]uint64)
	for _, line := range lines {
		for _, tok := range tokenRe.FindAllString(strings.ToLower(line), -1) {
			freq[tok]++
		}
	}
	keys := make([]string, 0, len(freq))
	for k := range freq {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var checksum uint64
	for _, k := range keys {
		checksum = (checksum + (wordHash(k)*freq[k])%mod) % mod
	}
	return checksum
}

func sumPrimes(limit int) uint64 {
	if limit < 2 {
		return 0
	}
	sieve := make([]bool, limit+1)
	for i := 2; i <= limit; i++ {
		sieve[i] = true
	}
	for p := 2; p*p <= limit; p++ {
		if !sieve[p] {
			continue
		}
		for i := p * p; i <= limit; i += p {
			sieve[i] = false
		}
	}
	var sum uint64
	for i := 2; i <= limit; i++ {
		if sieve[i] {
			sum += uint64(i)
		}
	}
	return sum
}

func checksumBytes(data []byte) uint64 {
	var h uint64
	for _, b := range data {
		h = (h*257 + uint64(b)) % mod
	}
	return h
}

func fillMatrixLCG(n int, seed uint32, valueMod int) []int {
	total := n * n
	out := make([]int, total)
	x := seed
	for i := 0; i < total; i++ {
		x = x*1664525 + 1013904223
		out[i] = int(x % uint32(valueMod))
	}
	return out
}

func matmulThreadedChecksum(a []int, b []int, n int, threads int) uint64 {
	if threads < 1 {
		threads = 1
	}
	if threads > n {
		threads = n
	}
	c := make([]int, n*n)
	var wg sync.WaitGroup
	for w := 0; w < threads; w++ {
		startRow := (w * n) / threads
		endRow := ((w + 1) * n) / threads
		wg.Add(1)
		go func(rs int, re int) {
			defer wg.Done()
			for i := rs; i < re; i++ {
				base := i * n
				for j := 0; j < n; j++ {
					sum := 0
					for k := 0; k < n; k++ {
						sum += a[base+k] * b[k*n+j]
					}
					c[base+j] = sum
				}
			}
		}(startRow, endRow)
	}
	wg.Wait()

	var checksum uint64
	for i, v := range c {
		term := (uint64(v) * uint64(i+1)) % mod
		checksum = (checksum + term) % mod
	}
	return checksum
}

type LifeInput struct {
	grid  [][]int
	steps int
}

func gameOfLifeChecksum(base [][]int, steps int) int64 {
	rows := len(base)
	cols := len(base[0])
	grid := make([][]int, rows)
	next := make([][]int, rows)
	for r := 0; r < rows; r++ {
		grid[r] = append([]int(nil), base[r]...)
		next[r] = make([]int, cols)
	}
	for s := 0; s < steps; s++ {
		for r := 0; r < rows; r++ {
			for c := 0; c < cols; c++ {
				neighbors := 0
				for dr := -1; dr <= 1; dr++ {
					for dc := -1; dc <= 1; dc++ {
						if dr == 0 && dc == 0 {
							continue
						}
						nr := r + dr
						nc := c + dc
						if nr >= 0 && nr < rows && nc >= 0 && nc < cols {
							neighbors += grid[nr][nc]
						}
					}
				}
				if grid[r][c] == 1 {
					if neighbors == 2 || neighbors == 3 {
						next[r][c] = 1
					} else {
						next[r][c] = 0
					}
				} else if neighbors == 3 {
					next[r][c] = 1
				} else {
					next[r][c] = 0
				}
			}
		}
		grid, next = next, grid
	}
	var checksum int64
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if grid[r][c] == 1 {
				checksum += int64(r*cols + c + 1)
			}
		}
	}
	return checksum
}

func readLines(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	lines := []string{}
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		lines = append(lines, line)
	}
	return lines, scanner.Err()
}

func mustReadNumbers(path string) []int {
	lines, err := readLines(path)
	if err != nil {
		panic(err)
	}
	out := make([]int, 0, len(lines))
	for _, l := range lines {
		v, err := strconv.Atoi(l)
		if err != nil {
			panic(err)
		}
		out = append(out, v)
	}
	return out
}

func mustReadLife(path string) LifeInput {
	lines, err := readLines(path)
	if err != nil {
		panic(err)
	}
	header := strings.Fields(lines[0])
	rows, _ := strconv.Atoi(header[0])
	cols, _ := strconv.Atoi(header[1])
	steps, _ := strconv.Atoi(header[2])
	grid := make([][]int, rows)
	for r := 0; r < rows; r++ {
		row := make([]int, cols)
		for c := 0; c < cols; c++ {
			if lines[r+1][c] == '1' {
				row[c] = 1
			}
		}
		grid[r] = row
	}
	return LifeInput{grid: grid, steps: steps}
}

func main() {
	workload := flag.String("workload", "", "")
	input := flag.String("input", "", "")
	runs := flag.Int("runs", 1, "")
	threads := flag.Int("threads", 1, "")
	flag.Parse()
	if *workload == "" || *input == "" || *runs < 1 || *threads < 1 {
		fmt.Fprintln(os.Stderr, "Usage: benchmark --workload <name> --input <file> --runs <n> --threads <n>")
		os.Exit(1)
	}

	var nValue int
	var numbers []int
	var lines []string
	var primeLimit int
	var life LifeInput
	var ioData []byte
	var matN int
	var matA []int
	var matB []int

	switch *workload {
	case "bubble", "quick", "merge":
		numbers = mustReadNumbers(*input)
		nValue = len(numbers)
	case "strings":
		var err error
		lines, err = readLines(*input)
		if err != nil {
			panic(err)
		}
		nValue = len(lines)
	case "primes":
		primeLines, err := readLines(*input)
		if err != nil {
			panic(err)
		}
		primeLimit, _ = strconv.Atoi(primeLines[0])
		nValue = primeLimit
	case "life":
		life = mustReadLife(*input)
		nValue = len(life.grid) * len(life.grid[0])
	case "io":
		var err error
		ioData, err = os.ReadFile(*input)
		if err != nil {
			panic(err)
		}
		nValue = len(ioData)
	case "matmul_mt":
		matLines, err := readLines(*input)
		if err != nil {
			panic(err)
		}
		fields := strings.Fields(matLines[0])
		if len(fields) != 4 {
			panic("invalid matmul_mt input")
		}
		matN, _ = strconv.Atoi(fields[0])
		seedA, _ := strconv.ParseUint(fields[1], 10, 32)
		seedB, _ := strconv.ParseUint(fields[2], 10, 32)
		valueMod, _ := strconv.Atoi(fields[3])
		matA = fillMatrixLCG(matN, uint32(seedA), valueMod)
		matB = fillMatrixLCG(matN, uint32(seedB), valueMod)
		nValue = matN
	default:
		fmt.Fprintln(os.Stderr, "unknown workload")
		os.Exit(1)
	}

	runTimes := make([]float64, 0, *runs)
	var checksum int64
	for i := 0; i < *runs; i++ {
		switch *workload {
		case "bubble":
			if !hasInversion(numbers) {
				panic("sort input is already sorted before run")
			}
			work := append([]int(nil), numbers...)
			start := time.Now()
			bubbleSort(work)
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
			checksum = checksumNumbers(work)
		case "quick":
			if !hasInversion(numbers) {
				panic("sort input is already sorted before run")
			}
			work := append([]int(nil), numbers...)
			start := time.Now()
			quickSort(work, 0, len(work)-1)
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
			checksum = checksumNumbers(work)
		case "merge":
			if !hasInversion(numbers) {
				panic("sort input is already sorted before run")
			}
			work := append([]int(nil), numbers...)
			start := time.Now()
			sorted := mergeSort(work)
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
			checksum = checksumNumbers(sorted)
		case "strings":
			start := time.Now()
			checksum = int64(checksumStrings(lines))
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
		case "primes":
			start := time.Now()
			checksum = int64(sumPrimes(primeLimit))
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
		case "life":
			start := time.Now()
			checksum = gameOfLifeChecksum(life.grid, life.steps)
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
		case "io":
			start := time.Now()
			checksum = int64(checksumBytes(ioData))
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
		case "matmul_mt":
			start := time.Now()
			checksum = int64(matmulThreadedChecksum(matA, matB, matN, *threads))
			runTimes = append(runTimes, float64(time.Since(start).Nanoseconds())/1_000_000.0)
		}
	}

	slowest := runTimes[0]
	total := 0.0
	for _, t := range runTimes {
		total += t
		if t > slowest {
			slowest = t
		}
	}
	effectiveRuns := *runs
	if *runs > 1 {
		total -= slowest
		effectiveRuns = *runs - 1
	}
	elapsed := total / float64(effectiveRuns)

	fmt.Printf(
		"LANG=go WORKLOAD=%s N=%d RUNS=%d THREADS=%d EFFECTIVE_RUNS=%d ELAPSED_MS=%.3f TOTAL_ELAPSED_MS=%.3f SLOWEST_MS=%.3f CHECKSUM=%d\n",
		*workload,
		nValue,
		*runs,
		*threads,
		effectiveRuns,
		elapsed,
		total,
		slowest,
		checksum,
	)
}
