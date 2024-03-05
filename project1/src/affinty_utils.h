#ifndef CORE_AFFINITY
#define CORE_AFFINITY

#ifdef WITH_CORE_AFFINITY

// Add core affinity dependency
#include <sched.h>
#define should_get_neighbour_thread(i) (i % 2)

const int thread_ids[32] = {0, 16, 2, 18, 4, 20, 6, 22, 8, 24, 10, 26, 12, 28, 14, 30, 1, 17, 3, 19, 5, 21, 7, 23, 9, 25, 11, 27, 13, 29, 15, 31};

/*
Gets the thread id by the given index.

It prioritizes getting thread ids that is on the same core.
*/
#define get_thread_id(i) (thread_ids[i])

#endif
#endif
