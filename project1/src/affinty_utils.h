#ifndef CORE_AFFINITY
#define CORE_AFFINITY

#ifdef WITH_CORE_AFFINITY

// Add core affinity dependency
#include <sched.h>
#define should_get_neighbour_thread(i) (i % 2)

/*
Gets the thread id by the given index.

It prioritizes getting thread ids that is on the same core.
*/
#define get_thread_id(i) ((should_get_neighbour_thread(i)) ? (15 + (i * 2)) : (i * 2))

#endif
#endif
