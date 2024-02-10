#include <stdio.h>
#include <stdlib.h>
#include "hash.h"
#include "test_data.h"

int main() {
    int num_tuples = 10;
    struct tuple* tuples = generate_tuples(num_tuples, 12);

    for (int i = 0; i < num_tuples; i++) {
        printf("partitioning_key: %lld, payload: %lld\n", tuples[i].partitioning_key, tuples[i].payload);
    }

    free(tuples);
    return 0;
}