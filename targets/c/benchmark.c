#include <ctype.h>
#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MOD 1000000007ULL

typedef struct {
    char **items;
    size_t len;
    size_t cap;
} StrList;

static void bubble_sort(int *values, size_t n) {
    for (size_t i = 0; i < n; i++) {
        int swapped = 0;
        for (size_t j = 0; j + 1 < n - i; j++) {
            if (values[j] > values[j + 1]) {
                int tmp = values[j];
                values[j] = values[j + 1];
                values[j + 1] = tmp;
                swapped = 1;
            }
        }
        if (!swapped) {
            break;
        }
    }
}

static int has_inversion(const int *values, size_t n) {
    for (size_t i = 1; i < n; i++) {
        if (values[i] < values[i - 1]) {
            return 1;
        }
    }
    return 0;
}

static void quick_sort(int *a, int lo, int hi) {
    if (lo >= hi) {
        return;
    }
    int i = lo;
    int j = hi;
    int pivot = a[(lo + hi) / 2];
    while (i <= j) {
        while (a[i] < pivot) i++;
        while (a[j] > pivot) j--;
        if (i <= j) {
            int t = a[i];
            a[i] = a[j];
            a[j] = t;
            i++;
            j--;
        }
    }
    if (lo < j) quick_sort(a, lo, j);
    if (i < hi) quick_sort(a, i, hi);
}

static void merge_sort_impl(int *a, int *tmp, int left, int right) {
    if (left >= right) return;
    int mid = (left + right) / 2;
    merge_sort_impl(a, tmp, left, mid);
    merge_sort_impl(a, tmp, mid + 1, right);
    int i = left;
    int j = mid + 1;
    int k = left;
    while (i <= mid && j <= right) {
        if (a[i] <= a[j]) {
            tmp[k++] = a[i++];
        } else {
            tmp[k++] = a[j++];
        }
    }
    while (i <= mid) tmp[k++] = a[i++];
    while (j <= right) tmp[k++] = a[j++];
    for (int p = left; p <= right; p++) a[p] = tmp[p];
}

static long long checksum_numbers(const int *values, size_t n) {
    long long sum = 0;
    for (size_t i = 0; i < n; i++) sum += values[i];
    return sum;
}

static unsigned long long word_hash(const char *word) {
    unsigned long long h = 0;
    for (const unsigned char *p = (const unsigned char *)word; *p; p++) {
        h = (h * 131ULL + (unsigned long long)(*p)) % MOD;
    }
    return h;
}

static int cmp_str_ptr(const void *a, const void *b) {
    const char *sa = *(const char * const *)a;
    const char *sb = *(const char * const *)b;
    return strcmp(sa, sb);
}

static void strlist_push(StrList *list, char *value) {
    if (list->len == list->cap) {
        size_t new_cap = list->cap == 0 ? 64 : list->cap * 2;
        char **grown = (char **)realloc(list->items, new_cap * sizeof(char *));
        if (!grown) {
            fprintf(stderr, "allocation failed\n");
            exit(1);
        }
        list->items = grown;
        list->cap = new_cap;
    }
    list->items[list->len++] = value;
}

static void tokenize_line(StrList *tokens, const char *line) {
    char buf[256];
    size_t n = 0;
    for (const unsigned char *p = (const unsigned char *)line; ; p++) {
        int ch = *p;
        if (isalnum(ch)) {
            if (n + 1 < sizeof(buf)) {
                buf[n++] = (char)tolower(ch);
            }
        } else {
            if (n > 0) {
                buf[n] = '\0';
                char *word = strdup(buf);
                if (!word) {
                    fprintf(stderr, "allocation failed\n");
                    exit(1);
                }
                strlist_push(tokens, word);
                n = 0;
            }
            if (ch == '\0') break;
        }
    }
}

static unsigned long long checksum_strings(char **lines, size_t line_count) {
    StrList tokens = {0};
    for (size_t i = 0; i < line_count; i++) {
        tokenize_line(&tokens, lines[i]);
    }
    qsort(tokens.items, tokens.len, sizeof(char *), cmp_str_ptr);
    unsigned long long checksum = 0;
    size_t i = 0;
    while (i < tokens.len) {
        size_t j = i + 1;
        while (j < tokens.len && strcmp(tokens.items[i], tokens.items[j]) == 0) j++;
        unsigned long long count = (unsigned long long)(j - i);
        checksum = (checksum + (word_hash(tokens.items[i]) * count) % MOD) % MOD;
        i = j;
    }
    for (size_t k = 0; k < tokens.len; k++) free(tokens.items[k]);
    free(tokens.items);
    return checksum;
}

static unsigned long long sum_primes(int limit) {
    if (limit < 2) return 0;
    unsigned char *sieve = (unsigned char *)calloc((size_t)limit + 1, 1);
    if (!sieve) {
        fprintf(stderr, "allocation failed\n");
        exit(1);
    }
    for (int i = 2; i <= limit; i++) sieve[i] = 1;
    for (int p = 2; p * p <= limit; p++) {
        if (!sieve[p]) continue;
        for (int i = p * p; i <= limit; i += p) sieve[i] = 0;
    }
    unsigned long long sum = 0;
    for (int i = 2; i <= limit; i++) if (sieve[i]) sum += (unsigned long long)i;
    free(sieve);
    return sum;
}

static unsigned long long checksum_bytes(const unsigned char *data, size_t len) {
    unsigned long long h = 0;
    for (size_t i = 0; i < len; i++) {
        h = (h * 257ULL + (unsigned long long)data[i]) % MOD;
    }
    return h;
}

static unsigned int lcg32(unsigned int x) {
    return x * 1664525u + 1013904223u;
}

typedef struct {
    int id;
    int a;
    int b;
    int first;
    int last;
} AllocItem;

static unsigned long long alloc_gc_checksum(int objects, int rounds, int payload_words, unsigned int seed) {
    unsigned long long checksum = 0;
    for (int r = 0; r < rounds; r++) {
        unsigned int base = (unsigned int)((unsigned long long)seed + (unsigned long long)r * 2654435761ULL);
        AllocItem *items = (AllocItem *)malloc((size_t)objects * sizeof(AllocItem));
        if (!items) {
            fprintf(stderr, "allocation failed\n");
            exit(1);
        }
        for (int i = 0; i < objects; i++) {
            unsigned int x = lcg32(base + (unsigned int)i);
            int first = 0;
            int last = 0;
            for (int p = 0; p < payload_words; p++) {
                unsigned int mask = (unsigned int)((unsigned long long)(p + 1) * 2246822519ULL);
                x = lcg32(x ^ mask);
                int v = (int)(x % 9973u);
                if (p == 0) first = v;
                last = v;
            }
            items[i].id = i;
            items[i].a = (int)(x % 1000003u);
            items[i].b = (int)((x >> 8) % 1000003u);
            items[i].first = first;
            items[i].last = last;
        }
        for (int i = 0; i < objects; i++) {
            unsigned long long term = (unsigned long long)(
                items[i].id * 17 + items[i].a * 31 + items[i].b * 47 + items[i].first * 73 + items[i].last * 89
            );
            checksum = (checksum + term) % MOD;
        }
        free(items);
    }
    return checksum;
}

static int **alloc_grid(int rows, int cols) {
    int **grid = (int **)malloc((size_t)rows * sizeof(int *));
    if (!grid) return NULL;
    for (int r = 0; r < rows; r++) {
        grid[r] = (int *)calloc((size_t)cols, sizeof(int));
        if (!grid[r]) return NULL;
    }
    return grid;
}

static void free_grid(int **grid, int rows) {
    for (int r = 0; r < rows; r++) free(grid[r]);
    free(grid);
}

static long long game_of_life_checksum(int **base, int rows, int cols, int steps) {
    int **grid = alloc_grid(rows, cols);
    int **next = alloc_grid(rows, cols);
    if (!grid || !next) {
        fprintf(stderr, "allocation failed\n");
        exit(1);
    }
    for (int r = 0; r < rows; r++) memcpy(grid[r], base[r], (size_t)cols * sizeof(int));
    for (int s = 0; s < steps; s++) {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                int n = 0;
                for (int dr = -1; dr <= 1; dr++) {
                    for (int dc = -1; dc <= 1; dc++) {
                        if (dr == 0 && dc == 0) continue;
                        int nr = r + dr;
                        int nc = c + dc;
                        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) n += grid[nr][nc];
                    }
                }
                if (grid[r][c]) {
                    next[r][c] = (n == 2 || n == 3) ? 1 : 0;
                } else {
                    next[r][c] = (n == 3) ? 1 : 0;
                }
            }
        }
        int **tmp = grid;
        grid = next;
        next = tmp;
    }
    long long checksum = 0;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (grid[r][c]) checksum += (long long)(r * cols + c + 1);
        }
    }
    free_grid(grid, rows);
    free_grid(next, rows);
    return checksum;
}

typedef struct {
    const int *a;
    const int *b;
    int *c;
    int n;
    int row_start;
    int row_end;
} MatMulTask;

static void fill_matrix_lcg(int *out, int n, unsigned int seed, int value_mod) {
    unsigned int x = seed;
    size_t total = (size_t)n * (size_t)n;
    for (size_t i = 0; i < total; i++) {
        x = x * 1664525u + 1013904223u;
        out[i] = (int)(x % (unsigned int)value_mod);
    }
}

static void *matmul_worker(void *arg) {
    MatMulTask *task = (MatMulTask *)arg;
    int n = task->n;
    for (int i = task->row_start; i < task->row_end; i++) {
        for (int j = 0; j < n; j++) {
            long long sum = 0;
            for (int k = 0; k < n; k++) {
                sum += (long long)task->a[i * n + k] * (long long)task->b[k * n + j];
            }
            task->c[i * n + j] = (int)sum;
        }
    }
    return NULL;
}

static unsigned long long matmul_threaded_checksum(const int *a, const int *b, int n, int threads) {
    int *c = (int *)malloc((size_t)n * (size_t)n * sizeof(int));
    if (!c) {
        fprintf(stderr, "allocation failed\n");
        exit(1);
    }
    int worker_count = threads < n ? threads : n;
    if (worker_count < 1) worker_count = 1;
    pthread_t *ids = (pthread_t *)malloc((size_t)worker_count * sizeof(pthread_t));
    MatMulTask *tasks = (MatMulTask *)malloc((size_t)worker_count * sizeof(MatMulTask));
    if (!ids || !tasks) {
        fprintf(stderr, "allocation failed\n");
        exit(1);
    }

    for (int w = 0; w < worker_count; w++) {
        int start = (w * n) / worker_count;
        int end = ((w + 1) * n) / worker_count;
        tasks[w].a = a;
        tasks[w].b = b;
        tasks[w].c = c;
        tasks[w].n = n;
        tasks[w].row_start = start;
        tasks[w].row_end = end;
        if (pthread_create(&ids[w], NULL, matmul_worker, &tasks[w]) != 0) {
            fprintf(stderr, "pthread_create failed\n");
            exit(1);
        }
    }
    for (int w = 0; w < worker_count; w++) {
        pthread_join(ids[w], NULL);
    }

    unsigned long long checksum = 0;
    size_t total = (size_t)n * (size_t)n;
    for (size_t i = 0; i < total; i++) {
        unsigned long long term = ((unsigned long long)c[i] * (unsigned long long)(i + 1)) % MOD;
        checksum = (checksum + term) % MOD;
    }
    free(ids);
    free(tasks);
    free(c);
    return checksum;
}

typedef struct {
    int start;
    int end;
    unsigned int seed;
    unsigned long long partial;
} ChannelTask;

static void *channel_worker(void *arg) {
    ChannelTask *task = (ChannelTask *)arg;
    unsigned long long local = 0;
    for (int i = task->start; i < task->end; i++) {
        unsigned int x = lcg32(task->seed + (unsigned int)i);
        local = (local + (unsigned long long)(x % (unsigned int)MOD)) % MOD;
    }
    task->partial = local;
    return NULL;
}

static unsigned long long channel_queue_checksum(int messages, unsigned int seed, int threads) {
    int worker_count = threads < 1 ? 1 : threads;
    pthread_t *ids = (pthread_t *)malloc((size_t)worker_count * sizeof(pthread_t));
    ChannelTask *tasks = (ChannelTask *)malloc((size_t)worker_count * sizeof(ChannelTask));
    if (!ids || !tasks) {
        fprintf(stderr, "allocation failed\n");
        exit(1);
    }
    for (int w = 0; w < worker_count; w++) {
        tasks[w].start = (w * messages) / worker_count;
        tasks[w].end = ((w + 1) * messages) / worker_count;
        tasks[w].seed = seed;
        tasks[w].partial = 0;
        if (pthread_create(&ids[w], NULL, channel_worker, &tasks[w]) != 0) {
            fprintf(stderr, "pthread_create failed\n");
            exit(1);
        }
    }
    unsigned long long checksum = 0;
    for (int w = 0; w < worker_count; w++) {
        pthread_join(ids[w], NULL);
        checksum = (checksum + tasks[w].partial) % MOD;
    }
    free(ids);
    free(tasks);
    return checksum;
}

static double elapsed_ms(struct timespec start, struct timespec end) {
    double seconds = (double)(end.tv_sec - start.tv_sec);
    double nanos = (double)(end.tv_nsec - start.tv_nsec);
    return seconds * 1000.0 + nanos / 1000000.0;
}

typedef struct {
    char *workload;
    char *input;
    int runs;
    int threads;
} Args;

static Args parse_args(int argc, char **argv) {
    Args args = {0};
    args.runs = 1;
    args.threads = 1;
    for (int i = 1; i < argc - 1; i += 2) {
        if (strcmp(argv[i], "--workload") == 0) args.workload = argv[i + 1];
        else if (strcmp(argv[i], "--input") == 0) args.input = argv[i + 1];
        else if (strcmp(argv[i], "--runs") == 0) args.runs = atoi(argv[i + 1]);
        else if (strcmp(argv[i], "--threads") == 0) args.threads = atoi(argv[i + 1]);
    }
    if (!args.workload || !args.input || args.runs < 1 || args.threads < 1) {
        fprintf(stderr, "Usage: benchmark --workload <name> --input <file> --runs <n> --threads <n>\n");
        exit(1);
    }
    return args;
}

int main(int argc, char **argv) {
    Args args = parse_args(argc, argv);
    FILE *f = fopen(args.input, "rb");
    if (!f) {
        fprintf(stderr, "Failed to open %s: %s\n", args.input, strerror(errno));
        return 1;
    }

    int *numbers = NULL;
    size_t numbers_len = 0;
    size_t numbers_cap = 0;
    char **lines = NULL;
    size_t lines_len = 0;
    size_t lines_cap = 0;
    int prime_limit = 0;
    int life_rows = 0, life_cols = 0, life_steps = 0;
    int **life_grid = NULL;
    unsigned char *io_data = NULL;
    size_t io_len = 0;
    int mat_n = 0;
    int mat_seed_a = 0;
    int mat_seed_b = 0;
    int mat_value_mod = 0;
    int *mat_a = NULL;
    int *mat_b = NULL;
    int alloc_objects = 0;
    int alloc_rounds = 0;
    int alloc_payload_words = 0;
    unsigned int alloc_seed = 0;
    int channel_messages = 0;
    int channel_queue_size = 0;
    unsigned int channel_seed = 0;

    if (strcmp(args.workload, "bubble") == 0 || strcmp(args.workload, "quick") == 0 || strcmp(args.workload, "merge") == 0) {
        char buf[128];
        while (fgets(buf, sizeof(buf), f)) {
            char *end = NULL;
            long v = strtol(buf, &end, 10);
            if (end == buf) continue;
            if (numbers_len == numbers_cap) {
                numbers_cap = numbers_cap == 0 ? 1024 : numbers_cap * 2;
                int *grown = (int *)realloc(numbers, numbers_cap * sizeof(int));
                if (!grown) return 1;
                numbers = grown;
            }
            numbers[numbers_len++] = (int)v;
        }
    } else if (strcmp(args.workload, "strings") == 0) {
        char buf[2048];
        while (fgets(buf, sizeof(buf), f)) {
            size_t len = strlen(buf);
            while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) buf[--len] = '\0';
            if (len == 0) continue;
            if (lines_len == lines_cap) {
                lines_cap = lines_cap == 0 ? 1024 : lines_cap * 2;
                char **grown = (char **)realloc(lines, lines_cap * sizeof(char *));
                if (!grown) return 1;
                lines = grown;
            }
            lines[lines_len++] = strdup(buf);
        }
    } else if (strcmp(args.workload, "primes") == 0) {
        if (fscanf(f, "%d", &prime_limit) != 1) {
            fprintf(stderr, "invalid primes input\n");
            return 1;
        }
    } else if (strcmp(args.workload, "life") == 0) {
        if (fscanf(f, "%d %d %d", &life_rows, &life_cols, &life_steps) != 3) {
            fprintf(stderr, "invalid life header\n");
            return 1;
        }
        life_grid = alloc_grid(life_rows, life_cols);
        if (!life_grid) return 1;
        char line[4096];
        fgets(line, sizeof(line), f);
        for (int r = 0; r < life_rows; r++) {
            if (!fgets(line, sizeof(line), f)) return 1;
            for (int c = 0; c < life_cols; c++) {
                life_grid[r][c] = (line[c] == '1') ? 1 : 0;
            }
        }
    } else if (strcmp(args.workload, "io") == 0) {
        if (fseek(f, 0, SEEK_END) != 0) return 1;
        long size = ftell(f);
        if (size < 0) return 1;
        if (fseek(f, 0, SEEK_SET) != 0) return 1;
        io_len = (size_t)size;
        io_data = (unsigned char *)malloc(io_len);
        if (!io_data) return 1;
        if (fread(io_data, 1, io_len, f) != io_len) return 1;
    } else if (strcmp(args.workload, "matmul_mt") == 0) {
        if (fscanf(f, "%d %d %d %d", &mat_n, &mat_seed_a, &mat_seed_b, &mat_value_mod) != 4) {
            fprintf(stderr, "invalid matmul_mt input\n");
            return 1;
        }
        if (mat_n < 1 || mat_value_mod < 2) {
            fprintf(stderr, "invalid matmul_mt parameters\n");
            return 1;
        }
        mat_a = (int *)malloc((size_t)mat_n * (size_t)mat_n * sizeof(int));
        mat_b = (int *)malloc((size_t)mat_n * (size_t)mat_n * sizeof(int));
        if (!mat_a || !mat_b) return 1;
        fill_matrix_lcg(mat_a, mat_n, (unsigned int)mat_seed_a, mat_value_mod);
        fill_matrix_lcg(mat_b, mat_n, (unsigned int)mat_seed_b, mat_value_mod);
    } else if (strcmp(args.workload, "alloc_gc") == 0) {
        if (fscanf(f, "%d %d %d %u", &alloc_objects, &alloc_rounds, &alloc_payload_words, &alloc_seed) != 4) {
            fprintf(stderr, "invalid alloc_gc input\n");
            return 1;
        }
    } else if (strcmp(args.workload, "channel_queue_mt") == 0) {
        if (fscanf(f, "%d %d %u", &channel_messages, &channel_queue_size, &channel_seed) != 3) {
            fprintf(stderr, "invalid channel_queue_mt input\n");
            return 1;
        }
        if (channel_queue_size < 1) {
            fprintf(stderr, "invalid channel_queue_mt parameters\n");
            return 1;
        }
    } else {
        fprintf(stderr, "unknown workload: %s\n", args.workload);
        return 1;
    }
    fclose(f);

    double *times = (double *)calloc((size_t)args.runs, sizeof(double));
    if (!times) return 1;
    long long checksum = 0;

    for (int run = 0; run < args.runs; run++) {
        struct timespec start, end;
        if (strcmp(args.workload, "bubble") == 0) {
            if (!has_inversion(numbers, numbers_len)) {
                fprintf(stderr, "sort input is already sorted before run\n");
                return 1;
            }
            int *work = (int *)malloc(numbers_len * sizeof(int));
            memcpy(work, numbers, numbers_len * sizeof(int));
            clock_gettime(CLOCK_MONOTONIC, &start);
            bubble_sort(work, numbers_len);
            clock_gettime(CLOCK_MONOTONIC, &end);
            checksum = checksum_numbers(work, numbers_len);
            free(work);
        } else if (strcmp(args.workload, "quick") == 0) {
            if (!has_inversion(numbers, numbers_len)) {
                fprintf(stderr, "sort input is already sorted before run\n");
                return 1;
            }
            int *work = (int *)malloc(numbers_len * sizeof(int));
            memcpy(work, numbers, numbers_len * sizeof(int));
            clock_gettime(CLOCK_MONOTONIC, &start);
            quick_sort(work, 0, (int)numbers_len - 1);
            clock_gettime(CLOCK_MONOTONIC, &end);
            checksum = checksum_numbers(work, numbers_len);
            free(work);
        } else if (strcmp(args.workload, "merge") == 0) {
            if (!has_inversion(numbers, numbers_len)) {
                fprintf(stderr, "sort input is already sorted before run\n");
                return 1;
            }
            int *work = (int *)malloc(numbers_len * sizeof(int));
            int *tmp = (int *)malloc(numbers_len * sizeof(int));
            memcpy(work, numbers, numbers_len * sizeof(int));
            clock_gettime(CLOCK_MONOTONIC, &start);
            merge_sort_impl(work, tmp, 0, (int)numbers_len - 1);
            clock_gettime(CLOCK_MONOTONIC, &end);
            checksum = checksum_numbers(work, numbers_len);
            free(work);
            free(tmp);
        } else if (strcmp(args.workload, "strings") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = (long long)checksum_strings(lines, lines_len);
            clock_gettime(CLOCK_MONOTONIC, &end);
        } else if (strcmp(args.workload, "primes") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = (long long)sum_primes(prime_limit);
            clock_gettime(CLOCK_MONOTONIC, &end);
        } else if (strcmp(args.workload, "life") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = game_of_life_checksum(life_grid, life_rows, life_cols, life_steps);
            clock_gettime(CLOCK_MONOTONIC, &end);
        } else if (strcmp(args.workload, "io") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = (long long)checksum_bytes(io_data, io_len);
            clock_gettime(CLOCK_MONOTONIC, &end);
        } else if (strcmp(args.workload, "matmul_mt") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = (long long)matmul_threaded_checksum(mat_a, mat_b, mat_n, args.threads);
            clock_gettime(CLOCK_MONOTONIC, &end);
        } else if (strcmp(args.workload, "alloc_gc") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = (long long)alloc_gc_checksum(alloc_objects, alloc_rounds, alloc_payload_words, alloc_seed);
            clock_gettime(CLOCK_MONOTONIC, &end);
        } else if (strcmp(args.workload, "channel_queue_mt") == 0) {
            clock_gettime(CLOCK_MONOTONIC, &start);
            checksum = (long long)channel_queue_checksum(channel_messages, channel_seed, args.threads);
            clock_gettime(CLOCK_MONOTONIC, &end);
        }
        times[run] = elapsed_ms(start, end);
    }

    double slowest = times[0];
    double total = 0.0;
    for (int i = 0; i < args.runs; i++) {
        total += times[i];
        if (times[i] > slowest) slowest = times[i];
    }
    int effective_runs = args.runs > 1 ? args.runs - 1 : 1;
    if (args.runs > 1) total -= slowest;
    double elapsed = total / (double)effective_runs;

    long long n_value = 0;
    if (strcmp(args.workload, "bubble") == 0 || strcmp(args.workload, "quick") == 0 || strcmp(args.workload, "merge") == 0) {
        n_value = (long long)numbers_len;
    } else if (strcmp(args.workload, "strings") == 0) {
        n_value = (long long)lines_len;
    } else if (strcmp(args.workload, "primes") == 0) {
        n_value = prime_limit;
    } else if (strcmp(args.workload, "life") == 0) {
        n_value = (long long)life_rows * life_cols;
    } else if (strcmp(args.workload, "io") == 0) {
        n_value = (long long)io_len;
    } else if (strcmp(args.workload, "matmul_mt") == 0) {
        n_value = (long long)mat_n;
    } else if (strcmp(args.workload, "alloc_gc") == 0) {
        n_value = (long long)alloc_objects;
    } else if (strcmp(args.workload, "channel_queue_mt") == 0) {
        n_value = (long long)channel_messages;
    }

    printf(
        "LANG=c WORKLOAD=%s N=%lld RUNS=%d THREADS=%d EFFECTIVE_RUNS=%d ELAPSED_MS=%.3f TOTAL_ELAPSED_MS=%.3f SLOWEST_MS=%.3f CHECKSUM=%lld\n",
        args.workload,
        n_value,
        args.runs,
        args.threads,
        effective_runs,
        elapsed,
        total,
        slowest,
        checksum
    );

    for (size_t i = 0; i < lines_len; i++) free(lines[i]);
    free(lines);
    free(numbers);
    free(io_data);
    free(mat_a);
    free(mat_b);
    free(times);
    if (life_grid) free_grid(life_grid, life_rows);
    return 0;
}
