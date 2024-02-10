#include <stdio.h>
#include <stdlib.h>
#include "hash.h"
#include "test_data.h"

#define SEED 1337
#define NUM_TUPLES 10

int main() {
    struct tuple* tuples = generate_tuples(NUM_TUPLES, SEED);

    for (int i = 0; i < NUM_TUPLES; i++) {
        printf("partitioning_key: %lld, payload: %lld\n", tuples[i].partitioning_key, tuples[i].payload);
    }

    free(tuples);
    return 0;
}