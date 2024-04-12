#ifndef BENCHMARK_HEADER
#define BENCHMARK_HEADER

#include <stdio.h>
#include <time.h>
#include "partitioning_algorithm.h"

struct timespec start, finish;

void bench_start() {
    clock_gettime(CLOCK_MONOTONIC_RAW, &start);
}

void bench_end() {
    clock_gettime(CLOCK_MONOTONIC_RAW, &finish);

    long elapsed_time_ms = (finish.tv_sec - start.tv_sec) * 1000 + (finish.tv_nsec - start.tv_nsec) / 1000000;

    printf("Elapsed: %lu ms\n", elapsed_time_ms);
}

void benchmark(partitioning_algorithm algorithm, struct partition_options *options) {
    algorithm(options, bench_start, bench_end);
}

#endif
