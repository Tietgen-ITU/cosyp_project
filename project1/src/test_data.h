#ifndef TEST_DATA_GEN
#define TEST_DATA_GEN

#include <stdint.h>

struct tuple {
    int64_t partitioning_key;
    int64_t payload;
};

// Returns a list of tuples with unique and uniformly distributed partitioning
// keys and random payloads. The specified seed is used for the random number
// generator.
struct tuple* generate_tuples(int num_tuples, int seed);

#endif