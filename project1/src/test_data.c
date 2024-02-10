#include <stdint.h>
#include <stdlib.h>
#include "test_data.h"

struct tuple* generate_tuples(int num_tuples, int seed) {
    struct tuple* tuples = (struct tuple*) malloc(num_tuples * sizeof(struct tuple));

    srand(seed);
    for (int i = 0; i < num_tuples; i++) {
        tuples[i].partitioning_key = i;
        tuples[i].payload = rand();
    }

    return tuples;
}
