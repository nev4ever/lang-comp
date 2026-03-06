using System.Text.RegularExpressions;

const long MOD = 1_000_000_007L;

static int Lcg32(int x) => unchecked(1664525 * x + 1013904223);

static bool HasInversion(int[] values)
{
    for (int i = 1; i < values.Length; i++)
    {
        if (values[i] < values[i - 1]) return true;
    }
    return false;
}

static void BubbleSort(int[] values)
{
    int n = values.Length;
    for (int i = 0; i < n; i++)
    {
        bool swapped = false;
        for (int j = 0; j < n - i - 1; j++)
        {
            if (values[j] > values[j + 1])
            {
                (values[j], values[j + 1]) = (values[j + 1], values[j]);
                swapped = true;
            }
        }
        if (!swapped) return;
    }
}

static void QuickSort(int[] values, int low, int high)
{
    if (low >= high) return;
    int i = low;
    int j = high;
    int pivot = values[(low + high) / 2];
    while (i <= j)
    {
        while (values[i] < pivot) i++;
        while (values[j] > pivot) j--;
        if (i <= j)
        {
            (values[i], values[j]) = (values[j], values[i]);
            i++;
            j--;
        }
    }
    if (low < j) QuickSort(values, low, j);
    if (i < high) QuickSort(values, i, high);
}

static int[] MergeSort(int[] values)
{
    if (values.Length <= 1) return values;
    int mid = values.Length / 2;
    int[] left = new int[mid];
    int[] right = new int[values.Length - mid];
    Array.Copy(values, 0, left, 0, mid);
    Array.Copy(values, mid, right, 0, values.Length - mid);
    left = MergeSort(left);
    right = MergeSort(right);
    int[] merged = new int[values.Length];
    int i = 0, j = 0, k = 0;
    while (i < left.Length && j < right.Length)
    {
        if (left[i] <= right[j]) merged[k++] = left[i++];
        else merged[k++] = right[j++];
    }
    while (i < left.Length) merged[k++] = left[i++];
    while (j < right.Length) merged[k++] = right[j++];
    return merged;
}

static long ChecksumNumbers(int[] values)
{
    long sum = 0;
    foreach (int v in values) sum += v;
    return sum;
}

static long WordHash(string word)
{
    long h = 0;
    foreach (char ch in word)
    {
        h = (h * 131 + ch) % MOD;
    }
    return h;
}

static long ChecksumStrings(List<string> lines)
{
    Dictionary<string, long> freq = new();
    foreach (string line in lines)
    {
        foreach (Match m in Regex.Matches(line.ToLowerInvariant(), "[a-z0-9]+"))
        {
            string tok = m.Value;
            freq[tok] = freq.GetValueOrDefault(tok) + 1;
        }
    }
    List<string> keys = [.. freq.Keys];
    keys.Sort(StringComparer.Ordinal);
    long checksum = 0;
    foreach (string key in keys)
    {
        checksum = (checksum + (WordHash(key) * freq[key]) % MOD) % MOD;
    }
    return checksum;
}

static long SumPrimes(int limit)
{
    if (limit < 2) return 0;
    bool[] sieve = new bool[limit + 1];
    for (int i = 2; i <= limit; i++) sieve[i] = true;
    for (int p = 2; p * p <= limit; p++)
    {
        if (!sieve[p]) continue;
        for (int i = p * p; i <= limit; i += p) sieve[i] = false;
    }
    long sum = 0;
    for (int i = 2; i <= limit; i++) if (sieve[i]) sum += i;
    return sum;
}

static long ChecksumBytes(byte[] data)
{
    long h = 0;
    foreach (byte b in data)
    {
        h = (h * 257 + b) % MOD;
    }
    return h;
}

static long GameOfLifeChecksum(int[][] baseGrid, int steps)
{
    int rows = baseGrid.Length;
    int cols = baseGrid[0].Length;
    int[][] grid = new int[rows][];
    int[][] next = new int[rows][];
    for (int r = 0; r < rows; r++)
    {
        grid[r] = new int[cols];
        next[r] = new int[cols];
        Array.Copy(baseGrid[r], grid[r], cols);
    }

    for (int s = 0; s < steps; s++)
    {
        for (int r = 0; r < rows; r++)
        {
            for (int c = 0; c < cols; c++)
            {
                int neighbors = 0;
                for (int dr = -1; dr <= 1; dr++)
                {
                    for (int dc = -1; dc <= 1; dc++)
                    {
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
        (grid, next) = (next, grid);
    }

    long checksum = 0;
    for (int r = 0; r < rows; r++)
    {
        for (int c = 0; c < cols; c++)
        {
            if (grid[r][c] == 1) checksum += (long)r * cols + c + 1;
        }
    }
    return checksum;
}

static int[] FillMatrixLCG(int n, uint seed, int valueMod)
{
    int[] outv = new int[n * n];
    uint x = seed;
    for (int i = 0; i < outv.Length; i++)
    {
        x = unchecked(x * 1664525u + 1013904223u);
        outv[i] = (int)(x % (uint)valueMod);
    }
    return outv;
}

static long MatmulThreadedChecksum(int[] a, int[] b, int n, int threads)
{
    int workerCount = Math.Max(1, Math.Min(threads, n));
    int[] c = new int[n * n];
    Task[] tasks = new Task[workerCount];
    for (int w = 0; w < workerCount; w++)
    {
        int startRow = (w * n) / workerCount;
        int endRow = ((w + 1) * n) / workerCount;
        tasks[w] = Task.Run(() =>
        {
            for (int i = startRow; i < endRow; i++)
            {
                int baseRow = i * n;
                for (int j = 0; j < n; j++)
                {
                    int sum = 0;
                    for (int k = 0; k < n; k++) sum += a[baseRow + k] * b[k * n + j];
                    c[baseRow + j] = sum;
                }
            }
        });
    }
    Task.WaitAll(tasks);

    long checksum = 0;
    for (int i = 0; i < c.Length; i++)
    {
        long term = ((long)c[i] * (i + 1L)) % MOD;
        checksum = (checksum + term) % MOD;
    }
    return checksum;
}

static long AllocGcChecksum(int objects, int rounds, int payloadWords, uint seed)
{
    long checksum = 0;
    for (int r = 0; r < rounds; r++)
    {
        uint baseSeed = (uint)((seed + (uint)r * 2654435761u));
        int[] idArr = new int[objects];
        int[] aArr = new int[objects];
        int[] bArr = new int[objects];
        int[] firstArr = new int[objects];
        int[] lastArr = new int[objects];
        for (int i = 0; i < objects; i++)
        {
            int x = Lcg32((int)(baseSeed + (uint)i));
            int first = 0;
            int last = 0;
            for (int p = 0; p < payloadWords; p++)
            {
                int mask = unchecked((int)((uint)(p + 1) * 2246822519u));
                x = Lcg32(x ^ mask);
                int v = (int)((uint)x % 9973u);
                if (p == 0) first = v;
                last = v;
            }
            idArr[i] = i;
            aArr[i] = (int)((uint)x % 1000003u);
            bArr[i] = (int)(((uint)x >> 8) % 1000003u);
            firstArr[i] = first;
            lastArr[i] = last;
        }

        for (int i = 0; i < objects; i++)
        {
            checksum = (checksum + idArr[i] * 17L + aArr[i] * 31L + bArr[i] * 47L + firstArr[i] * 73L + lastArr[i] * 89L) % MOD;
        }
    }
    return checksum;
}

static long ChannelQueueChecksum(int messages, uint seed, int threads)
{
    int workerCount = Math.Max(1, threads);
    long[] partial = new long[workerCount];
    Task[] tasks = new Task[workerCount];
    for (int t = 0; t < workerCount; t++)
    {
        int tid = t;
        int start = (t * messages) / workerCount;
        int end = ((t + 1) * messages) / workerCount;
        tasks[t] = Task.Run(() =>
        {
            long local = 0;
            for (int i = start; i < end; i++)
            {
                int x = Lcg32((int)(seed + (uint)i));
                local = (local + ((uint)x % MOD)) % MOD;
            }
            partial[tid] = local;
        });
    }
    Task.WaitAll(tasks);
    long checksum = 0;
    foreach (long p in partial) checksum = (checksum + p) % MOD;
    return checksum;
}

static List<string> ReadLines(string path)
{
    return File.ReadLines(path).Select(x => x.Trim()).Where(x => x.Length > 0).ToList();
}

static string ArgValue(string[] args, string key, string def)
{
    for (int i = 0; i + 1 < args.Length; i += 2)
    {
        if (args[i] == key) return args[i + 1];
    }
    return def;
}

string workload = ArgValue(args, "--workload", "");
string input = ArgValue(args, "--input", "");
int runs = int.Parse(ArgValue(args, "--runs", "1"));
int threads = int.Parse(ArgValue(args, "--threads", "1"));

if (string.IsNullOrEmpty(workload) || string.IsNullOrEmpty(input) || runs < 1 || threads < 1)
{
    Console.Error.WriteLine("Usage: Benchmark --workload <name> --input <file> --runs <n> --threads <n>");
    return;
}

int nValue = 0;
int[]? numbers = null;
List<string>? lines = null;
int primeLimit = 0;
int[][]? lifeGrid = null;
int lifeSteps = 0;
byte[]? ioData = null;
int matN = 0;
int[]? matA = null;
int[]? matB = null;
int allocObjects = 0;
int allocRounds = 0;
int allocPayloadWords = 0;
uint allocSeed = 0;
int channelMessages = 0;
uint channelSeed = 0;

if (workload is "bubble" or "quick" or "merge")
{
    numbers = ReadLines(input).Select(int.Parse).ToArray();
    nValue = numbers.Length;
}
else if (workload == "strings")
{
    lines = ReadLines(input);
    nValue = lines.Count;
}
else if (workload == "primes")
{
    primeLimit = int.Parse(ReadLines(input)[0]);
    nValue = primeLimit;
}
else if (workload == "life")
{
    List<string> raw = ReadLines(input);
    string[] header = raw[0].Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
    int rows = int.Parse(header[0]);
    int cols = int.Parse(header[1]);
    lifeSteps = int.Parse(header[2]);
    lifeGrid = new int[rows][];
    for (int r = 0; r < rows; r++)
    {
        lifeGrid[r] = new int[cols];
        string row = raw[r + 1];
        for (int c = 0; c < cols; c++) lifeGrid[r][c] = row[c] == '1' ? 1 : 0;
    }
    nValue = rows * cols;
}
else if (workload == "io")
{
    ioData = File.ReadAllBytes(input);
    nValue = ioData.Length;
}
else if (workload == "matmul_mt")
{
    string[] parts = ReadLines(input)[0].Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length != 4) throw new Exception("invalid matmul_mt input");
    matN = int.Parse(parts[0]);
    uint seedA = uint.Parse(parts[1]);
    uint seedB = uint.Parse(parts[2]);
    int valueMod = int.Parse(parts[3]);
    matA = FillMatrixLCG(matN, seedA, valueMod);
    matB = FillMatrixLCG(matN, seedB, valueMod);
    nValue = matN;
}
else if (workload == "alloc_gc")
{
    string[] parts = ReadLines(input)[0].Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length != 4) throw new Exception("invalid alloc_gc input");
    allocObjects = int.Parse(parts[0]);
    allocRounds = int.Parse(parts[1]);
    allocPayloadWords = int.Parse(parts[2]);
    allocSeed = uint.Parse(parts[3]);
    nValue = allocObjects;
}
else if (workload == "channel_queue_mt")
{
    string[] parts = ReadLines(input)[0].Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length != 3) throw new Exception("invalid channel_queue_mt input");
    channelMessages = int.Parse(parts[0]);
    channelSeed = uint.Parse(parts[2]);
    nValue = channelMessages;
}
else
{
    Console.Error.WriteLine("unknown workload");
    return;
}

double[] times = new double[runs];
long checksum = 0;

for (int run = 0; run < runs; run++)
{
    long start = System.Diagnostics.Stopwatch.GetTimestamp();

    if (workload == "bubble")
    {
        if (!HasInversion(numbers!)) throw new Exception("sort input is already sorted before run");
        int[] work = (int[])numbers!.Clone();
        BubbleSort(work);
        checksum = ChecksumNumbers(work);
    }
    else if (workload == "quick")
    {
        if (!HasInversion(numbers!)) throw new Exception("sort input is already sorted before run");
        int[] work = (int[])numbers!.Clone();
        QuickSort(work, 0, work.Length - 1);
        checksum = ChecksumNumbers(work);
    }
    else if (workload == "merge")
    {
        if (!HasInversion(numbers!)) throw new Exception("sort input is already sorted before run");
        int[] sorted = MergeSort((int[])numbers!.Clone());
        checksum = ChecksumNumbers(sorted);
    }
    else if (workload == "strings")
    {
        checksum = ChecksumStrings(lines!);
    }
    else if (workload == "primes")
    {
        checksum = SumPrimes(primeLimit);
    }
    else if (workload == "life")
    {
        checksum = GameOfLifeChecksum(lifeGrid!, lifeSteps);
    }
    else if (workload == "io")
    {
        checksum = ChecksumBytes(ioData!);
    }
    else if (workload == "matmul_mt")
    {
        checksum = MatmulThreadedChecksum(matA!, matB!, matN, threads);
    }
    else if (workload == "alloc_gc")
    {
        checksum = AllocGcChecksum(allocObjects, allocRounds, allocPayloadWords, allocSeed);
    }
    else if (workload == "channel_queue_mt")
    {
        checksum = ChannelQueueChecksum(channelMessages, channelSeed, threads);
    }

    long end = System.Diagnostics.Stopwatch.GetTimestamp();
    times[run] = (end - start) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
}

double slowest = times.Max();
double total = times.Sum();
int effectiveRuns = runs;
if (runs > 1)
{
    total -= slowest;
    effectiveRuns = runs - 1;
}
double elapsed = total / effectiveRuns;

Console.WriteLine(
    $"LANG=csharp WORKLOAD={workload} N={nValue} RUNS={runs} THREADS={threads} EFFECTIVE_RUNS={effectiveRuns} ELAPSED_MS={elapsed:F3} TOTAL_ELAPSED_MS={total:F3} SLOWEST_MS={slowest:F3} CHECKSUM={checksum}"
);
