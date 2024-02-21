#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "hash.h"
#include "test_data.h"
#include "partitioning_algorithm.h"
#include "independent_output.h"
#include "concurrent_output.h"
#include "benchmark.h"

#define SEED 1337

int main(int argc, char *argv[])
{
    size_t num_tuples = 0;
    size_t hash_bits = 0;
    size_t num_threads = 0;
    partitioning_algorithm algorithm = NULL;

    opterr = 0;
    int c;
    while ((c = getopt(argc, argv, "t:h:n:a:")) != -1)
    {
        switch (c)
        {
        case 't':
            num_threads = atoi(optarg);
            break;
        case 'h':
            hash_bits = atoi(optarg);
            break;
        case 'n':
            num_tuples = atoi(optarg);
            break;
        case 'a':
            if (strcmp(optarg, "independent") == 0)
            {
                algorithm = independent_output;
            }
            else if (strcmp(optarg, "concurrent") == 0)
            {
                algorithm = concurrent_output;
            }
            else
            {
                printf("Invalid algorithm: %s\n", optarg);
                return 1;
            }
            break;
        case '?':
            return 1;
        default:
            abort();
        }
    }

    if (num_tuples == 0 || hash_bits == 0 || num_threads == 0 || algorithm == NULL)
    {
        printf("Usage: %s -t <num_threads> -h <hash_bits> -n <num_tuples> -a <algorithm>\n", argv[0]);
        return 1;
    }

    struct tuple *tuples = generate_tuples(num_tuples, SEED);

    // for (int i = 0; i < NUM_TUPLES; i++) {
    //     printf("partitioning_key: %lld, payload: %lld\n", tuples[i].partitioning_key, tuples[i].payload);
    // }

    struct partition_options options = {
        .data = tuples,
        .data_length = num_tuples,
        .hash_bits = hash_bits,
        .num_threads = num_threads};

    printf("Running with:\n");
    printf("  tuples: %ld\n", num_tuples);
    printf("  hash bits: %ld\n", hash_bits);
    printf("  threads: %ld\n", num_threads);
    printf("  algorithm: %s\n", algorithm == independent_output ? "independent" : "concurrent");

    benchmark(algorithm, &options);

    free(tuples);
    return 0;
}