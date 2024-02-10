#include <stdio.h>
#include <stdlib.h>
#include "hash.h"
#include "test_data.h"
#include "partitioning_algorithm.h"
#include "independent_output.h"
#include "benchmark.h"

#define SEED 1337
#define NUM_TUPLES 10

int main() {
    struct tuple* tuples = generate_tuples(NUM_TUPLES, SEED);

    for (int i = 0; i < NUM_TUPLES; i++) {
        printf("partitioning_key: %lld, payload: %lld\n", tuples[i].partitioning_key, tuples[i].payload);
    }

    struct partition_options options = {
        .data = tuples,
        .data_length = NUM_TUPLES,
        .hash_bits = 4,
        .num_threads = 4
    };

    benchmark(independent_output, &options);
    // benchmark(concurrent_buffers, &options);

    free(tuples);
    return 0;
}