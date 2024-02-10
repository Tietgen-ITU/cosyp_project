#ifndef INDEPENDENT_OUTPUT
#define INDEPENDENT_OUTPUT

#include <stdio.h>
#include "partitioning_algorithm.h"

void independent_output(struct partition_options *options) {
    printf("%d\n", options->hash_bits);
}

#endif
