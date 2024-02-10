#ifndef PARTITIONING_ALGORITHM
#define PARTITIONING_ALGORITHM

#include "test_data.h"

struct partition_options {
    struct tuple *data;

    // The number of tuples in the data pointer
    int data_length;

    int hash_bits;
    int num_threads;
};

typedef void (*partitioning_algorithm)(struct partition_options *options);

#endif