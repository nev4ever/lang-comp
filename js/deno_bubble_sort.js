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

function checksum(values) {
  let sum = 0;
  for (const v of values) sum += v;
  return sum;
}

function readNumbers(path) {
  return Deno.readTextFileSync(path)
    .split(/\r?\n/)
    .filter(Boolean)
    .map((v) => Number.parseInt(v, 10));
}

if (import.meta.main) {
  const file = Deno.args[0];
  if (!file) {
    console.error("Usage: deno_bubble_sort.js <numbers_file>");
    Deno.exit(1);
  }

  const values = readNumbers(file);
  const start = performance.now();
  bubbleSort(values);
  const elapsedMs = performance.now() - start;

  console.log(`LANG=javascript N=${values.length} ELAPSED_MS=${elapsedMs.toFixed(3)} CHECKSUM=${checksum(values)}`);
}
