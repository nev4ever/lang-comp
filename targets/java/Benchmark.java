import java.io.BufferedReader;
import java.io.FileReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Benchmark {
    private static final long MOD = 1_000_000_007L;

    private static void bubbleSort(int[] values) {
        int n = values.length;
        for (int i = 0; i < n; i++) {
            boolean swapped = false;
            for (int j = 0; j < n - i - 1; j++) {
                if (values[j] > values[j + 1]) {
                    int t = values[j];
                    values[j] = values[j + 1];
                    values[j + 1] = t;
                    swapped = true;
                }
            }
            if (!swapped) return;
        }
    }

    private static boolean hasInversion(int[] values) {
        for (int i = 1; i < values.length; i++) {
            if (values[i] < values[i - 1]) return true;
        }
        return false;
    }

    private static void quickSort(int[] values, int low, int high) {
        if (low >= high) return;
        int pivot = values[(low + high) / 2];
        int i = low;
        int j = high;
        while (i <= j) {
            while (values[i] < pivot) i++;
            while (values[j] > pivot) j--;
            if (i <= j) {
                int t = values[i];
                values[i] = values[j];
                values[j] = t;
                i++;
                j--;
            }
        }
        if (low < j) quickSort(values, low, j);
        if (i < high) quickSort(values, i, high);
    }

    private static int[] mergeSort(int[] values) {
        if (values.length <= 1) return values;
        int mid = values.length / 2;
        int[] left = new int[mid];
        int[] right = new int[values.length - mid];
        System.arraycopy(values, 0, left, 0, mid);
        System.arraycopy(values, mid, right, 0, values.length - mid);
        left = mergeSort(left);
        right = mergeSort(right);
        int[] merged = new int[values.length];
        int i = 0;
        int j = 0;
        int k = 0;
        while (i < left.length && j < right.length) {
            if (left[i] <= right[j]) merged[k++] = left[i++];
            else merged[k++] = right[j++];
        }
        while (i < left.length) merged[k++] = left[i++];
        while (j < right.length) merged[k++] = right[j++];
        return merged;
    }

    private static long checksumNumbers(int[] values) {
        long sum = 0;
        for (int v : values) sum += v;
        return sum;
    }

    private static long wordHash(String word) {
        long h = 0;
        for (int i = 0; i < word.length(); i++) {
            h = (h * 131 + word.charAt(i)) % MOD;
        }
        return h;
    }

    private static long checksumStrings(List<String> lines) {
        Map<String, Long> freq = new HashMap<>();
        for (String line : lines) {
            String[] tokens = line.toLowerCase().split("[^a-z0-9]+");
            for (String token : tokens) {
                if (token.isEmpty()) continue;
                freq.put(token, freq.getOrDefault(token, 0L) + 1L);
            }
        }
        List<String> keys = new ArrayList<>(freq.keySet());
        Collections.sort(keys);
        long checksum = 0;
        for (String key : keys) {
            checksum = (checksum + (wordHash(key) * freq.get(key)) % MOD) % MOD;
        }
        return checksum;
    }

    private static long sumPrimes(int limit) {
        if (limit < 2) return 0;
        boolean[] sieve = new boolean[limit + 1];
        for (int i = 2; i <= limit; i++) sieve[i] = true;
        for (int p = 2; p * p <= limit; p++) {
            if (!sieve[p]) continue;
            for (int i = p * p; i <= limit; i += p) sieve[i] = false;
        }
        long sum = 0;
        for (int i = 2; i <= limit; i++) if (sieve[i]) sum += i;
        return sum;
    }

    private static long gameOfLifeChecksum(int[][] baseGrid, int steps) {
        int rows = baseGrid.length;
        int cols = baseGrid[0].length;
        int[][] grid = new int[rows][cols];
        int[][] next = new int[rows][cols];
        for (int r = 0; r < rows; r++) {
            System.arraycopy(baseGrid[r], 0, grid[r], 0, cols);
        }
        for (int s = 0; s < steps; s++) {
            for (int r = 0; r < rows; r++) {
                for (int c = 0; c < cols; c++) {
                    int neighbors = 0;
                    for (int dr = -1; dr <= 1; dr++) {
                        for (int dc = -1; dc <= 1; dc++) {
                            if (dr == 0 && dc == 0) continue;
                            int nr = r + dr;
                            int nc = c + dc;
                            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) neighbors += grid[nr][nc];
                        }
                    }
                    if (grid[r][c] == 1) next[r][c] = (neighbors == 2 || neighbors == 3) ? 1 : 0;
                    else next[r][c] = (neighbors == 3) ? 1 : 0;
                }
            }
            int[][] tmp = grid;
            grid = next;
            next = tmp;
        }
        long checksum = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 1) checksum += (long)r * cols + c + 1;
            }
        }
        return checksum;
    }

    private static long checksumBytes(byte[] data) {
        long h = 0;
        for (byte b : data) {
            h = (h * 257 + (b & 0xFF)) % MOD;
        }
        return h;
    }

    private static int lcg32(int x) {
        return 1664525 * x + 1013904223;
    }

    private static long allocGcChecksum(int objects, int rounds, int payloadWords, int seed) {
        long checksum = 0;
        class Item {
            int id;
            int a;
            int b;
            int first;
            int last;
            Item(int id, int a, int b, int first, int last) {
                this.id = id;
                this.a = a;
                this.b = b;
                this.first = first;
                this.last = last;
            }
        }
        for (int r = 0; r < rounds; r++) {
            int base = (int)((seed & 0xFFFFFFFFL) + (long)r * 2654435761L);
            Item[] items = new Item[objects];
            for (int i = 0; i < objects; i++) {
                int x = lcg32(base + i);
                int first = 0;
                int last = 0;
                for (int p = 0; p < payloadWords; p++) {
                    int mask = (int)((long)(p + 1) * 2246822519L);
                    x = lcg32(x ^ mask);
                    int v = Integer.remainderUnsigned(x, 9973);
                    if (p == 0) first = v;
                    last = v;
                }
                items[i] = new Item(
                    i,
                    Integer.remainderUnsigned(x, 1000003),
                    Integer.remainderUnsigned(x >>> 8, 1000003),
                    first,
                    last
                );
            }
            for (Item it : items) {
                checksum = (checksum + it.id * 17L + it.a * 31L + it.b * 47L + it.first * 73L + it.last * 89L) % MOD;
            }
        }
        return checksum;
    }

    private static long channelQueueChecksum(int messages, int seed, int threads) throws InterruptedException {
        int workerCount = Math.max(1, threads);
        long[] partials = new long[workerCount];
        Thread[] workers = new Thread[workerCount];
        for (int t = 0; t < workerCount; t++) {
            final int tid = t;
            final int start = (t * messages) / workerCount;
            final int end = ((t + 1) * messages) / workerCount;
            workers[t] = new Thread(() -> {
                long local = 0;
                for (int i = start; i < end; i++) {
                    int x = lcg32(seed + i);
                    local = (local + Integer.remainderUnsigned(x, (int)MOD)) % MOD;
                }
                partials[tid] = local;
            });
            workers[t].start();
        }
        for (Thread t : workers) {
            t.join();
        }
        long checksum = 0;
        for (long v : partials) checksum = (checksum + v) % MOD;
        return checksum;
    }

    private static int[] fillMatrixLCG(int n, int seed, int valueMod) {
        int[] out = new int[n * n];
        long x = seed & 0xFFFFFFFFL;
        for (int i = 0; i < out.length; i++) {
            x = (x * 1664525L + 1013904223L) & 0xFFFFFFFFL;
            out[i] = (int)(x % valueMod);
        }
        return out;
    }

    private static long matmulThreadedChecksum(int[] a, int[] b, int n, int threads) throws InterruptedException {
        int workerCount = Math.max(1, Math.min(threads, n));
        int[] c = new int[n * n];
        Thread[] workers = new Thread[workerCount];
        for (int w = 0; w < workerCount; w++) {
            final int startRow = (w * n) / workerCount;
            final int endRow = ((w + 1) * n) / workerCount;
            workers[w] = new Thread(() -> {
                for (int i = startRow; i < endRow; i++) {
                    int base = i * n;
                    for (int j = 0; j < n; j++) {
                        int sum = 0;
                        for (int k = 0; k < n; k++) {
                            sum += a[base + k] * b[k * n + j];
                        }
                        c[base + j] = sum;
                    }
                }
            });
            workers[w].start();
        }
        for (Thread t : workers) {
            t.join();
        }
        long checksum = 0;
        for (int i = 0; i < c.length; i++) {
            long term = ((long)c[i] * (i + 1L)) % MOD;
            checksum = (checksum + term) % MOD;
        }
        return checksum;
    }

    private static List<String> readLines(String path) throws Exception {
        List<String> out = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = br.readLine()) != null) {
                String trimmed = line.trim();
                if (!trimmed.isEmpty()) out.add(trimmed);
            }
        }
        return out;
    }

    private static String argValue(String[] args, String key, String def) {
        for (int i = 0; i < args.length - 1; i += 2) {
            if (args[i].equals(key)) return args[i + 1];
        }
        return def;
    }

    public static void main(String[] args) throws Exception {
        String workload = argValue(args, "--workload", "");
        String input = argValue(args, "--input", "");
        int runs = Integer.parseInt(argValue(args, "--runs", "1"));
        int threads = Integer.parseInt(argValue(args, "--threads", "1"));
        if (workload.isEmpty() || input.isEmpty() || runs < 1 || threads < 1) {
            System.err.println("Usage: Benchmark --workload <name> --input <file> --runs <n> --threads <n>");
            System.exit(1);
        }

        int nValue = 0;
        int[] numbers = null;
        List<String> lines = null;
        int primeLimit = 0;
        int[][] lifeGrid = null;
        int lifeSteps = 0;
        byte[] ioData = null;
        int matN = 0;
        int[] matA = null;
        int[] matB = null;
        int allocObjects = 0;
        int allocRounds = 0;
        int allocPayloadWords = 0;
        int allocSeed = 0;
        int channelMessages = 0;
        int channelSeed = 0;

        if (workload.equals("bubble") || workload.equals("quick") || workload.equals("merge")) {
            List<String> raw = readLines(input);
            numbers = new int[raw.size()];
            for (int i = 0; i < raw.size(); i++) numbers[i] = Integer.parseInt(raw.get(i));
            nValue = numbers.length;
        } else if (workload.equals("strings")) {
            lines = readLines(input);
            nValue = lines.size();
        } else if (workload.equals("primes")) {
            primeLimit = Integer.parseInt(readLines(input).get(0));
            nValue = primeLimit;
        } else if (workload.equals("life")) {
            List<String> raw = readLines(input);
            String[] header = raw.get(0).split("\\s+");
            int rows = Integer.parseInt(header[0]);
            int cols = Integer.parseInt(header[1]);
            lifeSteps = Integer.parseInt(header[2]);
            lifeGrid = new int[rows][cols];
            for (int r = 0; r < rows; r++) {
                String row = raw.get(r + 1);
                for (int c = 0; c < cols; c++) lifeGrid[r][c] = row.charAt(c) == '1' ? 1 : 0;
            }
            nValue = rows * cols;
        } else if (workload.equals("io")) {
            ioData = Files.readAllBytes(Path.of(input));
            nValue = ioData.length;
        } else if (workload.equals("matmul_mt")) {
            String[] fields = readLines(input).get(0).split("\\s+");
            if (fields.length != 4) throw new IllegalArgumentException("invalid matmul_mt input");
            matN = Integer.parseInt(fields[0]);
            int seedA = Integer.parseUnsignedInt(fields[1]);
            int seedB = Integer.parseUnsignedInt(fields[2]);
            int valueMod = Integer.parseInt(fields[3]);
            matA = fillMatrixLCG(matN, seedA, valueMod);
            matB = fillMatrixLCG(matN, seedB, valueMod);
            nValue = matN;
        } else if (workload.equals("alloc_gc")) {
            String[] fields = readLines(input).get(0).split("\\s+");
            if (fields.length != 4) throw new IllegalArgumentException("invalid alloc_gc input");
            allocObjects = Integer.parseInt(fields[0]);
            allocRounds = Integer.parseInt(fields[1]);
            allocPayloadWords = Integer.parseInt(fields[2]);
            allocSeed = Integer.parseUnsignedInt(fields[3]);
            nValue = allocObjects;
        } else if (workload.equals("channel_queue_mt")) {
            String[] fields = readLines(input).get(0).split("\\s+");
            if (fields.length != 3) throw new IllegalArgumentException("invalid channel_queue_mt input");
            channelMessages = Integer.parseInt(fields[0]);
            channelSeed = Integer.parseUnsignedInt(fields[2]);
            nValue = channelMessages;
        } else {
            System.err.println("unknown workload");
            System.exit(1);
        }

        double[] times = new double[runs];
        long checksum = 0;
        for (int run = 0; run < runs; run++) {
            long start = System.nanoTime();
            if (workload.equals("bubble")) {
                if (!hasInversion(numbers)) throw new IllegalStateException("sort input is already sorted before run");
                int[] work = numbers.clone();
                bubbleSort(work);
                checksum = checksumNumbers(work);
            } else if (workload.equals("quick")) {
                if (!hasInversion(numbers)) throw new IllegalStateException("sort input is already sorted before run");
                int[] work = numbers.clone();
                quickSort(work, 0, work.length - 1);
                checksum = checksumNumbers(work);
            } else if (workload.equals("merge")) {
                if (!hasInversion(numbers)) throw new IllegalStateException("sort input is already sorted before run");
                int[] sorted = mergeSort(numbers.clone());
                checksum = checksumNumbers(sorted);
            } else if (workload.equals("strings")) {
                checksum = checksumStrings(lines);
            } else if (workload.equals("primes")) {
                checksum = sumPrimes(primeLimit);
            } else if (workload.equals("life")) {
                checksum = gameOfLifeChecksum(lifeGrid, lifeSteps);
            } else if (workload.equals("io")) {
                checksum = checksumBytes(ioData);
            } else if (workload.equals("matmul_mt")) {
                checksum = matmulThreadedChecksum(matA, matB, matN, threads);
            } else if (workload.equals("alloc_gc")) {
                checksum = allocGcChecksum(allocObjects, allocRounds, allocPayloadWords, allocSeed);
            } else if (workload.equals("channel_queue_mt")) {
                checksum = channelQueueChecksum(channelMessages, channelSeed, threads);
            }
            times[run] = (System.nanoTime() - start) / 1_000_000.0;
        }

        double slowest = times[0];
        double total = 0.0;
        for (double t : times) {
            total += t;
            if (t > slowest) slowest = t;
        }
        int effectiveRuns = runs > 1 ? runs - 1 : 1;
        if (runs > 1) total -= slowest;
        double elapsed = total / effectiveRuns;

        System.out.printf(
            "LANG=java WORKLOAD=%s N=%d RUNS=%d THREADS=%d EFFECTIVE_RUNS=%d ELAPSED_MS=%.3f TOTAL_ELAPSED_MS=%.3f SLOWEST_MS=%.3f CHECKSUM=%d%n",
            workload,
            nValue,
            runs,
            threads,
            effectiveRuns,
            elapsed,
            total,
            slowest,
            checksum
        );
    }
}
