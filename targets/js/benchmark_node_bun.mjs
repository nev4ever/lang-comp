#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { performance } from "node:perf_hooks";
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";

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

function fillMatrixLCG(n, seed, valueMod) {
  const out = new Int32Array(n * n);
  let x = seed >>> 0;
  for (let i = 0; i < out.length; i += 1) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    out[i] = x % valueMod;
  }
  return out;
}

function matmulWorkerCompute(data) {
  const { aSab, bSab, cSab, n, rowStart, rowEnd } = data;
  const a = new Int32Array(aSab);
  const b = new Int32Array(bSab);
  const c = new Int32Array(cSab);
  for (let i = rowStart; i < rowEnd; i += 1) {
    const rowBase = i * n;
    for (let j = 0; j < n; j += 1) {
      let sum = 0;
      for (let k = 0; k < n; k += 1) {
        sum += a[rowBase + k] * b[k * n + j];
      }
      c[rowBase + j] = sum;
    }
  }
}

async function matmulThreadedChecksum(aBase, bBase, n, threads) {
  const workerCount = Math.max(1, Math.min(threads, n));
  const bytes = Int32Array.BYTES_PER_ELEMENT * n * n;
  const aSab = new SharedArrayBuffer(bytes);
  const bSab = new SharedArrayBuffer(bytes);
  const cSab = new SharedArrayBuffer(bytes);
  const a = new Int32Array(aSab);
  const b = new Int32Array(bSab);
  const c = new Int32Array(cSab);
  a.set(aBase);
  b.set(bBase);

  const workers = [];
  for (let w = 0; w < workerCount; w += 1) {
    const rowStart = Math.floor((w * n) / workerCount);
    const rowEnd = Math.floor(((w + 1) * n) / workerCount);
    workers.push(
      new Promise((resolve, reject) => {
        const worker = new Worker(new URL(import.meta.url), {
          workerData: { kind: "matmul", aSab, bSab, cSab, n, rowStart, rowEnd },
        });
        worker.once("message", () => resolve());
        worker.once("error", reject);
        worker.once("exit", (code) => {
          if (code !== 0) reject(new Error(`worker exited with code ${code}`));
        });
      }),
    );
  }
  await Promise.all(workers);
  let checksum = 0;
  for (let i = 0; i < c.length; i += 1) {
    checksum = (checksum + ((c[i] * (i + 1)) % MOD + MOD) % MOD) % MOD;
  }
  return checksum;
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
  const lines = readFileSync(path, "utf-8").split(/\r?\n/).map((v) => v.trim()).filter(Boolean);
  const [rowsS, colsS, stepsS] = lines[0].split(/\s+/);
  const rows = Number.parseInt(rowsS, 10);
  const cols = Number.parseInt(colsS, 10);
  const steps = Number.parseInt(stepsS, 10);
  const grid = [];
  for (let r = 0; r < rows; r += 1) {
    const line = lines[r + 1];
    const row = [];
    for (let c = 0; c < cols; c += 1) {
      row.push(line[c] === "1" ? 1 : 0);
    }
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
  for (let i = 2; i < argv.length; i += 2) {
    out[argv[i]] = argv[i + 1];
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  const workload = args["--workload"];
  const input = args["--input"];
  const runs = Number.parseInt(args["--runs"] || "1", 10);
  const threads = Number.parseInt(args["--threads"] || "1", 10);
  if (!workload || !input) {
    console.error("Usage: benchmark_node_bun.mjs --workload <name> --input <file> --runs <n> --threads <n>");
    process.exit(1);
  }
  if (!Number.isFinite(runs) || runs < 1 || !Number.isFinite(threads) || threads < 1) {
    console.error("runs and threads must be >= 1");
    process.exit(1);
  }

  let nValue = 0;
  let baseNumbers = null;
  let stringLines = null;
  let primeLimit = 0;
  let lifeGrid = null;
  let lifeSteps = 0;
  let ioBytes = null;
  let matN = 0;
  let matA = null;
  let matB = null;

  if (workload === "bubble" || workload === "quick" || workload === "merge") {
    baseNumbers = readFileSync(input, "utf-8").split(/\r?\n/).filter(Boolean).map((v) => Number.parseInt(v, 10));
    nValue = baseNumbers.length;
  } else if (workload === "strings") {
    stringLines = readFileSync(input, "utf-8").split(/\r?\n/).filter(Boolean);
    nValue = stringLines.length;
  } else if (workload === "primes") {
    primeLimit = Number.parseInt(readFileSync(input, "utf-8").split(/\r?\n/).find((line) => line.trim()) || "0", 10);
    nValue = primeLimit;
  } else if (workload === "life") {
    const parsed = parseLife(input);
    lifeGrid = parsed.grid;
    lifeSteps = parsed.steps;
    nValue = lifeGrid.length * (lifeGrid.length ? lifeGrid[0].length : 0);
  } else if (workload === "io") {
    ioBytes = readFileSync(input);
    nValue = ioBytes.length;
  } else if (workload === "matmul_mt") {
    const parts = readFileSync(input, "utf-8").trim().split(/\s+/);
    if (parts.length !== 4) {
      console.error("invalid matmul_mt input");
      process.exit(1);
    }
    matN = Number.parseInt(parts[0], 10);
    const seedA = Number.parseInt(parts[1], 10);
    const seedB = Number.parseInt(parts[2], 10);
    const valueMod = Number.parseInt(parts[3], 10);
    matA = fillMatrixLCG(matN, seedA, valueMod);
    matB = fillMatrixLCG(matN, seedB, valueMod);
    nValue = matN;
  } else {
    console.error(`unknown workload: ${workload}`);
    process.exit(1);
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
    } else if (workload === "matmul_mt") {
      const start = performance.now();
      checksum = await matmulThreadedChecksum(matA, matB, matN, threads);
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

if (!isMainThread) {
  if (workerData?.kind === "matmul") {
    matmulWorkerCompute(workerData);
    parentPort.postMessage("done");
  } else {
    throw new Error("unknown worker job");
  }
} else {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
