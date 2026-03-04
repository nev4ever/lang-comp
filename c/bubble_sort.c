#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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

static long long checksum(const int *values, size_t n) {
    long long sum = 0;
    for (size_t i = 0; i < n; i++) {
        sum += values[i];
    }
    return sum;
}

static double elapsed_ms(struct timespec start, struct timespec end) {
    double seconds = (double)(end.tv_sec - start.tv_sec);
    double nanos = (double)(end.tv_nsec - start.tv_nsec);
    return seconds * 1000.0 + nanos / 1000000.0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: bubble_sort <numbers_file>\n");
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        fprintf(stderr, "Failed to open %s: %s\n", argv[1], strerror(errno));
        return 1;
    }

    size_t capacity = 1024;
    size_t n = 0;
    int *values = malloc(capacity * sizeof(int));
    if (!values) {
        fclose(f);
        fprintf(stderr, "Allocation failed\n");
        return 1;
    }

    char line[128];
    while (fgets(line, sizeof(line), f)) {
        if (n == capacity) {
            capacity *= 2;
            int *grown = realloc(values, capacity * sizeof(int));
            if (!grown) {
                free(values);
                fclose(f);
                fprintf(stderr, "Reallocation failed\n");
                return 1;
            }
            values = grown;
        }
        values[n++] = atoi(line);
    }
    fclose(f);

    struct timespec start;
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    bubble_sort(values, n);
    clock_gettime(CLOCK_MONOTONIC, &end);

    printf("LANG=c N=%zu ELAPSED_MS=%.3f CHECKSUM=%lld\n", n, elapsed_ms(start, end), checksum(values, n));

    free(values);
    return 0;
}
