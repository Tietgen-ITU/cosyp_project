#include <stdio.h>

int hash(int key, int num_bits) {
    return key % (1 << (num_bits - 1));
}