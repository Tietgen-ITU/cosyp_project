#ifndef CONCURRENT_OUTPUT
#define CONCURRENT_OUTPUT

#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <stdatomic.h>
#include "hash.h"
#include "partitioning_algorithm.h"

// Add core affinity utils and dependencies
#ifdef WITH_CORE_AFFINITY
#include <sched.h>
#include "affinity_utils.h"
#endif

struct concurrent_output_worker_args
{
    struct tuple *data;
    size_t length;
    int thread_num;
    int hash_bits;

    atomic_size_t *partition_lengths;
    struct tuple **partitions;
};

void *concurrent_worker(void *arguments);

void concurrent_output(struct partition_options *options, void bench_start(), void bench_end())
{
    size_t num_partitions = (1 << options->hash_bits);
    atomic_size_t *partition_lengths = (atomic_size_t *)malloc(num_partitions * sizeof(atomic_size_t));
    struct tuple **partitions = (struct tuple **)malloc(num_partitions * sizeof(struct tuple *));

#ifdef WITH_CORE_AFFINITY
    // Create cpu masks to define which thread to run on
    cpu_set_t *cpuset = malloc(options->num_threads * sizeof(cpu_set_t));
#endif

    size_t expected_size = options->data_length / num_partitions;
    // TODO: re-evaluate. In our case its perfectly uniform.
    size_t partition_space = expected_size;
    for (int i = 0; i < num_partitions; i++)
    {
        partitions[i] = (struct tuple *)malloc(partition_space * sizeof(struct tuple));
        partition_lengths[i] = 0;
    }

    pthread_t *threads = (pthread_t *)malloc(options->num_threads * sizeof(pthread_t));
    pthread_attr_t *attr = (pthread_attr_t *)malloc(options->num_threads * sizeof(pthread_attr_t));
    struct concurrent_output_worker_args *args = (struct concurrent_output_worker_args *)malloc(options->num_threads * sizeof(struct concurrent_output_worker_args));

    bench_start();

    for (int i = 0; i < options->num_threads; i++)
    {
        // Assume data_length is divisible by num_threads
        size_t length = options->data_length / options->num_threads;
        struct tuple *data = options->data + (i * length);

        args[i] = (struct concurrent_output_worker_args){
            .data = data,
            .length = length,
            .thread_num = i,
            .hash_bits = options->hash_bits,
            .partition_lengths = partition_lengths,
            .partitions = partitions};

        if (pthread_attr_init(&attr[i]))
        {
            printf("Error initialising thread attributes %d - aborting\n", i);
            goto cleanup;
        }

#ifdef WITH_CORE_AFFINITY
        // Set the core affinity for the thread
        int thread_id = get_thread_id(i);
        printf("Setting core affinity for thread %d\n", i);
        CPU_ZERO(cpuset[i]);           // Reset the cpu set mask
        CPU_SET(thread_id, cpuset[i]); // Set the cpu mask to point at the thread_id

        // Apply core affinity info to the thread
        pthread_attr_setaffinity_np(&attr[i], sizeof(cpu_set_t), &cpuset[i]);
#endif

        if (pthread_create(&threads[i], &attr[i], concurrent_worker, &args[i]))
        {
            printf("Error creating thread %d - aborting\n", i);
            goto cleanup;
        }
    }

    for (int i = 0; i < options->num_threads; i++)
    {
        pthread_join(threads[i], NULL);
        pthread_attr_destroy(&attr[i]);
    }

    bench_end();

cleanup:
    for (int i = 0; i < num_partitions; i++)
        free(partitions[i]);
    free(partitions);
    free(partition_lengths);

    free(threads);
    free(attr);
    free(args);
}

void *concurrent_worker(void *arguments)
{
    struct concurrent_output_worker_args args = *((struct concurrent_output_worker_args *)arguments);

    for (size_t i = 0; i < args.length; i++)
    {
        int64_t partition_index = hash(args.data[i].partitioning_key, args.hash_bits);
        size_t cur_partition_length = atomic_fetch_add(&args.partition_lengths[partition_index], 1);
        args.partitions[partition_index][cur_partition_length] = args.data[i];
    }

    return NULL;
}

#endif
