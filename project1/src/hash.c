#include <stdio.h>

int hash(int key, int num_bits) {
    return key % num_bits;
}