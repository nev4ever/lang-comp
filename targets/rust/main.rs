use std::collections::HashMap;
use std::fs;
use std::sync::Arc;
use std::thread;
use std::time::Instant;

const MOD: u64 = 1_000_000_007;

fn lcg32(x: u32) -> u32 {
    x.wrapping_mul(1664525).wrapping_add(1013904223)
}

fn has_inversion(values: &[i32]) -> bool {
    for i in 1..values.len() {
        if values[i] < values[i - 1] {
            return true;
        }
    }
    false
}

fn bubble_sort(values: &mut [i32]) {
    let n = values.len();
    for i in 0..n {
        let mut swapped = false;
        for j in 0..(n - i - 1) {
            if values[j] > values[j + 1] {
                values.swap(j, j + 1);
                swapped = true;
            }
        }
        if !swapped {
            return;
        }
    }
}

fn quick_sort(values: &mut [i32], low: isize, high: isize) {
    if low >= high {
        return;
    }
    let mut i = low;
    let mut j = high;
    let pivot = values[((low + high) / 2) as usize];
    while i <= j {
        while values[i as usize] < pivot {
            i += 1;
        }
        while values[j as usize] > pivot {
            j -= 1;
        }
        if i <= j {
            values.swap(i as usize, j as usize);
            i += 1;
            j -= 1;
        }
    }
    if low < j {
        quick_sort(values, low, j);
    }
    if i < high {
        quick_sort(values, i, high);
    }
}

fn merge_sort(values: &[i32]) -> Vec<i32> {
    if values.len() <= 1 {
        return values.to_vec();
    }
    let mid = values.len() / 2;
    let left = merge_sort(&values[..mid]);
    let right = merge_sort(&values[mid..]);
    let mut merged = Vec::with_capacity(values.len());
    let mut i = 0;
    let mut j = 0;
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            merged.push(left[i]);
            i += 1;
        } else {
            merged.push(right[j]);
            j += 1;
        }
    }
    merged.extend_from_slice(&left[i..]);
    merged.extend_from_slice(&right[j..]);
    merged
}

fn checksum_numbers(values: &[i32]) -> i64 {
    values.iter().map(|v| *v as i64).sum()
}

fn word_hash(word: &str) -> u64 {
    let mut h = 0_u64;
    for ch in word.chars() {
        h = (h * 131 + ch as u64) % MOD;
    }
    h
}

fn checksum_strings(lines: &[String]) -> u64 {
    let mut freq: HashMap<String, u64> = HashMap::new();
    for line in lines {
        let mut token = String::new();
        for ch in line.chars().flat_map(|c| c.to_lowercase()) {
            if ch.is_ascii_alphanumeric() {
                token.push(ch);
            } else if !token.is_empty() {
                *freq.entry(token.clone()).or_insert(0) += 1;
                token.clear();
            }
        }
        if !token.is_empty() {
            *freq.entry(token).or_insert(0) += 1;
        }
    }

    let mut keys: Vec<String> = freq.keys().cloned().collect();
    keys.sort();
    let mut checksum = 0_u64;
    for key in keys {
        let count = *freq.get(&key).unwrap_or(&0);
        checksum = (checksum + (word_hash(&key) * count) % MOD) % MOD;
    }
    checksum
}

fn sum_primes(limit: usize) -> u64 {
    if limit < 2 {
        return 0;
    }
    let mut sieve = vec![true; limit + 1];
    sieve[0] = false;
    sieve[1] = false;
    let mut p = 2;
    while p * p <= limit {
        if sieve[p] {
            let mut i = p * p;
            while i <= limit {
                sieve[i] = false;
                i += p;
            }
        }
        p += 1;
    }
    let mut sum = 0_u64;
    for (i, is_prime) in sieve.iter().enumerate().skip(2) {
        if *is_prime {
            sum += i as u64;
        }
    }
    sum
}

fn checksum_bytes(data: &[u8]) -> u64 {
    let mut h = 0_u64;
    for b in data {
        h = (h * 257 + *b as u64) % MOD;
    }
    h
}

fn game_of_life_checksum(base_grid: &[Vec<u8>], steps: usize) -> i64 {
    let rows = base_grid.len();
    let cols = if rows > 0 { base_grid[0].len() } else { 0 };
    let mut grid = base_grid.to_vec();
    let mut next = vec![vec![0_u8; cols]; rows];

    for _ in 0..steps {
        for r in 0..rows {
            for c in 0..cols {
                let mut neighbors = 0_u8;
                for dr in -1_i32..=1 {
                    for dc in -1_i32..=1 {
                        if dr == 0 && dc == 0 {
                            continue;
                        }
                        let nr = r as i32 + dr;
                        let nc = c as i32 + dc;
                        if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                            neighbors += grid[nr as usize][nc as usize];
                        }
                    }
                }
                if grid[r][c] == 1 {
                    next[r][c] = if neighbors == 2 || neighbors == 3 { 1 } else { 0 };
                } else {
                    next[r][c] = if neighbors == 3 { 1 } else { 0 };
                }
            }
        }
        std::mem::swap(&mut grid, &mut next);
    }

    let mut checksum = 0_i64;
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] == 1 {
                checksum += (r * cols + c + 1) as i64;
            }
        }
    }
    checksum
}

fn fill_matrix_lcg(n: usize, seed: u32, value_mod: i32) -> Vec<i32> {
    let mut out = vec![0_i32; n * n];
    let mut x = seed;
    for v in &mut out {
        x = lcg32(x);
        *v = (x % value_mod as u32) as i32;
    }
    out
}

fn matmul_threaded_checksum(a: &[i32], b: &[i32], n: usize, threads: usize) -> i64 {
    let worker_count = threads.max(1).min(n.max(1));
    let a_arc = Arc::new(a.to_vec());
    let b_arc = Arc::new(b.to_vec());
    let mut handles = Vec::with_capacity(worker_count);

    for w in 0..worker_count {
        let start_row = (w * n) / worker_count;
        let end_row = ((w + 1) * n) / worker_count;
        let a_cl = Arc::clone(&a_arc);
        let b_cl = Arc::clone(&b_arc);
        handles.push(thread::spawn(move || -> u64 {
            let mut local = 0_u64;
            for i in start_row..end_row {
                let base = i * n;
                for j in 0..n {
                    let mut sum = 0_i64;
                    for k in 0..n {
                        sum += a_cl[base + k] as i64 * b_cl[k * n + j] as i64;
                    }
                    let idx = (base + j + 1) as u64;
                    let term = ((sum as u64) * idx) % MOD;
                    local = (local + term) % MOD;
                }
            }
            local
        }));
    }

    let mut checksum = 0_u64;
    for h in handles {
        if let Ok(v) = h.join() {
            checksum = (checksum + v) % MOD;
        }
    }
    checksum as i64
}

fn alloc_gc_checksum(objects: usize, rounds: usize, payload_words: usize, seed: u32) -> i64 {
    let mut checksum = 0_u64;
    for r in 0..rounds {
        let base = seed.wrapping_add((r as u32).wrapping_mul(2654435761));
        let mut items: Vec<(usize, u32, u32, u32, u32)> = Vec::with_capacity(objects);
        for i in 0..objects {
            let mut x = lcg32(base.wrapping_add(i as u32));
            let mut first = 0_u32;
            let mut last = 0_u32;
            for p in 0..payload_words {
                let mask = ((p as u32).wrapping_add(1)).wrapping_mul(2246822519);
                x = lcg32(x ^ mask);
                let v = x % 9973;
                if p == 0 {
                    first = v;
                }
                last = v;
            }
            items.push((
                i,
                x % 1_000_003,
                (x >> 8) % 1_000_003,
                first,
                last,
            ));
        }
        for it in items {
            let term = it.0 as u64 * 17
                + it.1 as u64 * 31
                + it.2 as u64 * 47
                + it.3 as u64 * 73
                + it.4 as u64 * 89;
            checksum = (checksum + term) % MOD;
        }
    }
    checksum as i64
}

fn channel_queue_checksum(messages: usize, seed: u32, threads: usize) -> i64 {
    let worker_count = threads.max(1);
    let mut handles = Vec::with_capacity(worker_count);
    for t in 0..worker_count {
        let start = (t * messages) / worker_count;
        let end = ((t + 1) * messages) / worker_count;
        handles.push(thread::spawn(move || -> u64 {
            let mut local = 0_u64;
            for i in start..end {
                let x = lcg32(seed.wrapping_add(i as u32));
                local = (local + (x as u64 % MOD)) % MOD;
            }
            local
        }));
    }
    let mut checksum = 0_u64;
    for h in handles {
        if let Ok(v) = h.join() {
            checksum = (checksum + v) % MOD;
        }
    }
    checksum as i64
}

fn read_non_empty_lines(path: &str) -> Vec<String> {
    fs::read_to_string(path)
        .unwrap_or_default()
        .lines()
        .map(|l| l.trim().to_string())
        .filter(|l| !l.is_empty())
        .collect()
}

fn arg_value(args: &[String], key: &str, default: &str) -> String {
    let mut i = 0;
    while i + 1 < args.len() {
        if args[i] == key {
            return args[i + 1].clone();
        }
        i += 2;
    }
    default.to_string()
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let workload = arg_value(&args, "--workload", "");
    let input = arg_value(&args, "--input", "");
    let runs: usize = arg_value(&args, "--runs", "1").parse().unwrap_or(1);
    let threads: usize = arg_value(&args, "--threads", "1").parse().unwrap_or(1);

    if workload.is_empty() || input.is_empty() || runs < 1 || threads < 1 {
        eprintln!("Usage: benchmark --workload <name> --input <file> --runs <n> --threads <n>");
        std::process::exit(1);
    }

    let n_value: usize;
    let mut numbers: Vec<i32> = Vec::new();
    let mut lines: Vec<String> = Vec::new();
    let mut prime_limit: usize = 0;
    let mut life_grid: Vec<Vec<u8>> = Vec::new();
    let mut life_steps: usize = 0;
    let mut io_data: Vec<u8> = Vec::new();
    let mut mat_n: usize = 0;
    let mut mat_a: Vec<i32> = Vec::new();
    let mut mat_b: Vec<i32> = Vec::new();
    let mut alloc_objects: usize = 0;
    let mut alloc_rounds: usize = 0;
    let mut alloc_payload_words: usize = 0;
    let mut alloc_seed: u32 = 0;
    let mut channel_messages: usize = 0;
    let mut channel_seed: u32 = 0;

    if workload == "bubble" || workload == "quick" || workload == "merge" {
        numbers = read_non_empty_lines(&input)
            .iter()
            .map(|x| x.parse::<i32>().unwrap_or(0))
            .collect();
        n_value = numbers.len();
    } else if workload == "strings" {
        lines = read_non_empty_lines(&input);
        n_value = lines.len();
    } else if workload == "primes" {
        let raw = read_non_empty_lines(&input);
        prime_limit = raw.first().and_then(|x| x.parse::<usize>().ok()).unwrap_or(0);
        n_value = prime_limit;
    } else if workload == "life" {
        let raw = read_non_empty_lines(&input);
        let header: Vec<usize> = raw
            .first()
            .map(|h| h.split_whitespace().filter_map(|v| v.parse::<usize>().ok()).collect())
            .unwrap_or_default();
        if header.len() != 3 {
            eprintln!("invalid life input");
            std::process::exit(1);
        }
        let rows = header[0];
        let cols = header[1];
        life_steps = header[2];
        life_grid = vec![vec![0_u8; cols]; rows];
        for r in 0..rows {
            let row = raw.get(r + 1).cloned().unwrap_or_default();
            for (c, ch) in row.chars().enumerate().take(cols) {
                life_grid[r][c] = if ch == '1' { 1 } else { 0 };
            }
        }
        n_value = rows * cols;
    } else if workload == "io" {
        io_data = fs::read(&input).unwrap_or_default();
        n_value = io_data.len();
    } else if workload == "matmul_mt" {
        let raw = read_non_empty_lines(&input);
        let parts: Vec<u64> = raw
            .first()
            .map(|h| h.split_whitespace().filter_map(|v| v.parse::<u64>().ok()).collect())
            .unwrap_or_default();
        if parts.len() != 4 {
            eprintln!("invalid matmul_mt input");
            std::process::exit(1);
        }
        mat_n = parts[0] as usize;
        mat_a = fill_matrix_lcg(mat_n, parts[1] as u32, parts[3] as i32);
        mat_b = fill_matrix_lcg(mat_n, parts[2] as u32, parts[3] as i32);
        n_value = mat_n;
    } else if workload == "alloc_gc" {
        let raw = read_non_empty_lines(&input);
        let parts: Vec<u64> = raw
            .first()
            .map(|h| h.split_whitespace().filter_map(|v| v.parse::<u64>().ok()).collect())
            .unwrap_or_default();
        if parts.len() != 4 {
            eprintln!("invalid alloc_gc input");
            std::process::exit(1);
        }
        alloc_objects = parts[0] as usize;
        alloc_rounds = parts[1] as usize;
        alloc_payload_words = parts[2] as usize;
        alloc_seed = parts[3] as u32;
        n_value = alloc_objects;
    } else if workload == "channel_queue_mt" {
        let raw = read_non_empty_lines(&input);
        let parts: Vec<u64> = raw
            .first()
            .map(|h| h.split_whitespace().filter_map(|v| v.parse::<u64>().ok()).collect())
            .unwrap_or_default();
        if parts.len() != 3 {
            eprintln!("invalid channel_queue_mt input");
            std::process::exit(1);
        }
        channel_messages = parts[0] as usize;
        channel_seed = parts[2] as u32;
        n_value = channel_messages;
    } else {
        eprintln!("unknown workload");
        std::process::exit(1);
    }

    let mut times: Vec<f64> = Vec::with_capacity(runs);
    let mut checksum: i64 = 0;

    for _ in 0..runs {
        let start = Instant::now();
        match workload.as_str() {
            "bubble" => {
                if !has_inversion(&numbers) {
                    eprintln!("sort input is already sorted before run");
                    std::process::exit(1);
                }
                let mut work = numbers.clone();
                bubble_sort(&mut work);
                checksum = checksum_numbers(&work);
            }
            "quick" => {
                if !has_inversion(&numbers) {
                    eprintln!("sort input is already sorted before run");
                    std::process::exit(1);
                }
                let mut work = numbers.clone();
                if !work.is_empty() {
                    let hi = work.len() as isize - 1;
                    quick_sort(&mut work, 0, hi);
                }
                checksum = checksum_numbers(&work);
            }
            "merge" => {
                if !has_inversion(&numbers) {
                    eprintln!("sort input is already sorted before run");
                    std::process::exit(1);
                }
                let sorted = merge_sort(&numbers);
                checksum = checksum_numbers(&sorted);
            }
            "strings" => checksum = checksum_strings(&lines) as i64,
            "primes" => checksum = sum_primes(prime_limit) as i64,
            "life" => checksum = game_of_life_checksum(&life_grid, life_steps),
            "io" => checksum = checksum_bytes(&io_data) as i64,
            "matmul_mt" => checksum = matmul_threaded_checksum(&mat_a, &mat_b, mat_n, threads),
            "alloc_gc" => checksum = alloc_gc_checksum(alloc_objects, alloc_rounds, alloc_payload_words, alloc_seed),
            "channel_queue_mt" => checksum = channel_queue_checksum(channel_messages, channel_seed, threads),
            _ => {
                eprintln!("unknown workload");
                std::process::exit(1);
            }
        }
        times.push(start.elapsed().as_secs_f64() * 1000.0);
    }

    let mut slowest = times[0];
    let mut total: f64 = times.iter().sum();
    for t in &times {
        if *t > slowest {
            slowest = *t;
        }
    }
    let effective_runs = if runs > 1 { runs - 1 } else { 1 };
    if runs > 1 {
        total -= slowest;
    }
    let elapsed = total / effective_runs as f64;

    println!(
        "LANG=rust WORKLOAD={} N={} RUNS={} THREADS={} EFFECTIVE_RUNS={} ELAPSED_MS={:.3} TOTAL_ELAPSED_MS={:.3} SLOWEST_MS={:.3} CHECKSUM={}",
        workload, n_value, runs, threads, effective_runs, elapsed, total, slowest, checksum
    );
}
