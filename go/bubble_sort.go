package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

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
			break
		}
	}
}

func checksum(values []int) int64 {
	var sum int64
	for _, v := range values {
		sum += int64(v)
	}
	return sum
}

func readNumbers(path string) ([]int, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var values []int
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		v, err := strconv.Atoi(line)
		if err != nil {
			return nil, err
		}
		values = append(values, v)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return values, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: bubble_sort <numbers_file>")
		os.Exit(1)
	}

	values, err := readNumbers(os.Args[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "read failed: %v\n", err)
		os.Exit(1)
	}

	start := time.Now()
	bubbleSort(values)
	elapsedMs := float64(time.Since(start).Nanoseconds()) / 1_000_000.0

	fmt.Printf("LANG=go N=%d ELAPSED_MS=%.3f CHECKSUM=%d\n", len(values), elapsedMs, checksum(values))
}
