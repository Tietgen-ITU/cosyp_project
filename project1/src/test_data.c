#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include "test_data.h"

void swap(struct tuple *a, struct tuple *b);
void shuffle(struct tuple* arr, size_t length);

struct tuple* generate_tuples(int num_tuples, int seed) {
    assert((num_tuples & (num_tuples - 1)) == 0);

    struct tuple* tuples = (struct tuple*) malloc(num_tuples * sizeof(struct tuple));

    srand(seed);
    for (int i = 0; i < num_tuples; i++) {
        tuples[i].partitioning_key = i;
        tuples[i].payload = rand();
    }

    shuffle(tuples, num_tuples);

    return tuples;
}

// Taken from https://www.geeksforgeeks.org/shuffle-a-given-array-using-fisher-yates-shuffle-algorithm/
void shuffle(struct tuple* arr, size_t length) {
    for (int i = length-1; i > 0; i--) {
        int j = rand() % (i+1);
        swap(&arr[i], &arr[j]);
    }
}

void swap(struct tuple *a, struct tuple *b) {
    struct tuple temp = *a;
    *a = *b;
    *b = temp;
}
