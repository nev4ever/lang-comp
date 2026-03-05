const MOD = 1_000_000_007;

function bubbleSort(values) {
  const n = values.length;
  for (let i = 0; i < n; i += 1) {
    let swapped = false;
    for (let j = 0; j < n - i - 1; j += 1) {
      if (values[j] > values[j + 1]) {
        const tmp = values[j];
        values[j] = values[j + 1];
        values[j + 1] = tmp;
        swapped = true;
      }
    }
    if (!swapped) break;
  }
}

function hasInversion(values) {
  for (let i = 1; i < values.length; i += 1) {
    if (values[i] < values[i - 1]) return true;
  }
  return false;
}

function quickSort(values, low, high) {
  if (low >= high) return;
  const pivot = values[(low + high) >> 1];
  let i = low;
  let j = high;
  while (i <= j) {
    while (values[i] < pivot) i += 1;
    while (values[j] > pivot) j -= 1;
    if (i <= j) {
      const tmp = values[i];
      values[i] = values[j];
      values[j] = tmp;
      i += 1;
      j -= 1;
    }
  }
  if (low < j) quickSort(values, low, j);
  if (i < high) quickSort(values, i, high);
}

function mergeSort(values) {
  if (values.length <= 1) return values;
  const mid = Math.floor(values.length / 2);
  const left = mergeSort(values.slice(0, mid));
  const right = mergeSort(values.slice(mid));
  const merged = [];
  let i = 0;
  let j = 0;
  while (i < left.length && j < right.length) {
    if (left[i] <= right[j]) {
      merged.push(left[i]);
      i += 1;
    } else {
      merged.push(right[j]);
      j += 1;
    }
  }
  while (i < left.length) merged.push(left[i++]);
  while (j < right.length) merged.push(right[j++]);
  return merged;
}

function checksumNumbers(values) {
  let sum = 0;
  for (const v of values) sum += v;
  return sum;
}

function wordHash(word) {
  let h = 0;
  for (let i = 0; i < word.length; i += 1) {
    h = (h * 131 + word.charCodeAt(i)) % MOD;
  }
  return h;
}

function checksumStrings(lines) {
  const freq = new Map();
  for (const line of lines) {
    const tokens = line.toLowerCase().match(/[a-z0-9]+/g) || [];
    for (const token of tokens) {
      freq.set(token, (freq.get(token) || 0) + 1);
    }
  }
  const keys = [...freq.keys()].sort();
  let checksum = 0;
  for (const key of keys) {
    checksum = (checksum + (wordHash(key) * freq.get(key)) % MOD) % MOD;
  }
  return checksum;
}

function checksumBytes(bytes) {
  let h = 0;
  for (let i = 0; i < bytes.length; i += 1) {
    h = (h * 257 + bytes[i]) % MOD;
  }
  return h;
}

function sumPrimes(limit) {
  if (limit < 2) return 0;
  const sieve = new Uint8Array(limit + 1);
  sieve.fill(1, 2);
  for (let p = 2; p * p <= limit; p += 1) {
    if (sieve[p]) {
      for (let i = p * p; i <= limit; i += p) sieve[i] = 0;
    }
  }
  let sum = 0;
  for (let i = 2; i <= limit; i += 1) {
    if (sieve[i]) sum += i;
  }
  return sum;
}

function parseLife(path) {
  const lines = Deno.readTextFileSync(path).split(/\r?\n/).map((v) => v.trim()).filter(Boolean);
  const [rowsS, colsS, stepsS] = lines[0].split(/\s+/);
  const rows = Number.parseInt(rowsS, 10);
  const cols = Number.parseInt(colsS, 10);
  const steps = Number.parseInt(stepsS, 10);
  const grid = [];
  for (let r = 0; r < rows; r += 1) {
    const line = lines[r + 1];
    const row = [];
    for (let c = 0; c < cols; c += 1) row.push(line[c] === "1" ? 1 : 0);
    grid.push(row);
  }
  return { grid, steps };
}

function gameOfLifeChecksum(baseGrid, steps) {
  const rows = baseGrid.length;
  const cols = rows ? baseGrid[0].length : 0;
  let grid = baseGrid.map((row) => row.slice());
  let next = Array.from({ length: rows }, () => Array(cols).fill(0));
  for (let s = 0; s < steps; s += 1) {
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        let neighbors = 0;
        for (let dr = -1; dr <= 1; dr += 1) {
          for (let dc = -1; dc <= 1; dc += 1) {
            if (dr === 0 && dc === 0) continue;
            const nr = r + dr;
            const nc = c + dc;
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) neighbors += grid[nr][nc];
          }
        }
        if (grid[r][c] === 1) {
          next[r][c] = neighbors === 2 || neighbors === 3 ? 1 : 0;
        } else {
          next[r][c] = neighbors === 3 ? 1 : 0;
        }
      }
    }
    const tmp = grid;
    grid = next;
    next = tmp;
  }
  let checksum = 0;
  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < cols; c += 1) {
      if (grid[r][c] === 1) checksum += r * cols + c + 1;
    }
  }
  return checksum;
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) {
    out[argv[i]] = argv[i + 1];
  }
  return out;
}

if (import.meta.main) {
  const args = parseArgs(Deno.args);
  const workload = args["--workload"];
  const input = args["--input"];
  const runs = Number.parseInt(args["--runs"] || "1", 10);
  const threads = Number.parseInt(args["--threads"] || "1", 10);
  if (!workload || !input) {
    console.error("Usage: benchmark_deno.js --workload <name> --input <file> --runs <n> --threads <n>");
    Deno.exit(1);
  }
  if (!Number.isFinite(runs) || runs < 1 || !Number.isFinite(threads) || threads < 1) {
    console.error("runs and threads must be >= 1");
    Deno.exit(1);
  }

  let nValue = 0;
  let baseNumbers = null;
  let stringLines = null;
  let primeLimit = 0;
  let lifeGrid = null;
  let lifeSteps = 0;
  let ioBytes = null;

  if (workload === "bubble" || workload === "quick" || workload === "merge") {
    baseNumbers = Deno.readTextFileSync(input).split(/\r?\n/).filter(Boolean).map((v) => Number.parseInt(v, 10));
    nValue = baseNumbers.length;
  } else if (workload === "strings") {
    stringLines = Deno.readTextFileSync(input).split(/\r?\n/).filter(Boolean);
    nValue = stringLines.length;
  } else if (workload === "primes") {
    primeLimit = Number.parseInt(Deno.readTextFileSync(input).split(/\r?\n/).find((line) => line.trim()) || "0", 10);
    nValue = primeLimit;
  } else if (workload === "life") {
    const parsed = parseLife(input);
    lifeGrid = parsed.grid;
    lifeSteps = parsed.steps;
    nValue = lifeGrid.length * (lifeGrid.length ? lifeGrid[0].length : 0);
  } else if (workload === "io") {
    ioBytes = Deno.readFileSync(input);
    nValue = ioBytes.length;
  } else {
    console.error(`unknown workload: ${workload}`);
    Deno.exit(1);
  }

  const runTimes = [];
  let checksum = 0;
  for (let run = 0; run < runs; run += 1) {
    if (workload === "bubble") {
      if (!hasInversion(baseNumbers)) throw new Error("sort input is already sorted before run");
      const values = baseNumbers.slice();
      const start = performance.now();
      bubbleSort(values);
      runTimes.push(performance.now() - start);
      checksum = checksumNumbers(values);
    } else if (workload === "quick") {
      if (!hasInversion(baseNumbers)) throw new Error("sort input is already sorted before run");
      const values = baseNumbers.slice();
      const start = performance.now();
      quickSort(values, 0, values.length - 1);
      runTimes.push(performance.now() - start);
      checksum = checksumNumbers(values);
    } else if (workload === "merge") {
      if (!hasInversion(baseNumbers)) throw new Error("sort input is already sorted before run");
      const values = baseNumbers.slice();
      const start = performance.now();
      const sorted = mergeSort(values);
      runTimes.push(performance.now() - start);
      checksum = checksumNumbers(sorted);
    } else if (workload === "strings") {
      const start = performance.now();
      checksum = checksumStrings(stringLines);
      runTimes.push(performance.now() - start);
    } else if (workload === "primes") {
      const start = performance.now();
      checksum = sumPrimes(primeLimit);
      runTimes.push(performance.now() - start);
    } else if (workload === "life") {
      const start = performance.now();
      checksum = gameOfLifeChecksum(lifeGrid, lifeSteps);
      runTimes.push(performance.now() - start);
    } else if (workload === "io") {
      const start = performance.now();
      checksum = checksumBytes(ioBytes);
      runTimes.push(performance.now() - start);
    }
  }

  const slowest = Math.max(...runTimes);
  let total;
  let effectiveRuns;
  if (runs > 1) {
    total = runTimes.reduce((a, b) => a + b, 0) - slowest;
    effectiveRuns = runs - 1;
  } else {
    total = runTimes[0];
    effectiveRuns = 1;
  }
  const elapsed = total / effectiveRuns;
  console.log(
    `LANG=javascript WORKLOAD=${workload} N=${nValue} RUNS=${runs} THREADS=${threads} EFFECTIVE_RUNS=${effectiveRuns} ELAPSED_MS=${elapsed.toFixed(3)} TOTAL_ELAPSED_MS=${total.toFixed(3)} SLOWEST_MS=${slowest.toFixed(3)} CHECKSUM=${checksum}`,
  );
}
