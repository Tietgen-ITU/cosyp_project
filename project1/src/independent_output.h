#ifndef INDEPENDENT_OUTPUT
#define INDEPENDENT_OUTPUT

#include <stdio.h>
#include <pthread.h>
#include <math.h>
#include "hash.h"
#include "partitioning_algorithm.h"

// Add core affinity utils and dependencies
#ifdef WITH_CORE_AFFINITY
#include <sched.h>
#include "affinity_utils.c"
#endif

struct independent_output_worker_args
{
    struct tuple *data;
    size_t length;
    int thread_num;
    int hash_bits;
};

void *independent_output_worker(void *arguments);

void independent_output(struct partition_options *options)
{
    pthread_t *threads = malloc(options->num_threads * sizeof(pthread_t));
    pthread_attr_t *attr = malloc(options->num_threads * sizeof(pthread_attr_t));
    struct independent_output_worker_args *args = malloc(options->num_threads * sizeof(struct independent_output_worker_args));

#ifdef WITH_CORE_AFFINITY
    // Create cpu masks to define which thread to run on
    cpu_set_t *cpuset = malloc(options->num_threads * sizeof(cpu_set_t));
#endif

    for (int i = 0; i < options->num_threads; i++)
    {
        // Assume data_length is divisible by num_threads
        size_t length = options->data_length / options->num_threads;
        struct tuple *data = options->data + (i * length);

        args[i] = (struct independent_output_worker_args){
            .data = data,
            .length = length,
            .thread_num = i,
            .hash_bits = options->hash_bits};

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

        if (pthread_create(&threads[i], &attr[i], independent_output_worker, &args[i]))
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

cleanup:
    free(threads);
    free(attr);
    free(args);
#ifdef WITH_CORE_AFFINITY
    free(cpuset);
#endif
}

void *independent_output_worker(void *arguments)
{
    struct independent_output_worker_args args = *((struct independent_output_worker_args *)arguments);
    size_t num_partitions = (1 << args.hash_bits);
    size_t expected_size = args.length / num_partitions;

    // TODO: re-evaluate. 4x to minimise probability of exceeding buffer size.
    // Could do wrap-around and overwrite previous entries? But this is wrong.
    size_t partition_space = expected_size * 4;

    size_t *partition_lengths = malloc(num_partitions * sizeof(size_t));
    struct tuple **partitions = malloc(num_partitions * sizeof(struct tuple *));
    for (int i = 0; i < num_partitions; i++)
    {
        partitions[i] = malloc(partition_space * sizeof(struct tuple));
        partition_lengths[i] = 0;
    }

    for (size_t i = 0; i < args.length; i++)
    {
        int64_t partition_index = hash(args.data[i].partitioning_key, args.hash_bits);
        size_t cur_partition_length = partition_lengths[partition_index];
        partitions[partition_index][cur_partition_length] = args.data[i];
        partition_lengths[partition_index]++;
    }

    // debug print
    // pthread_mutex_lock(&lock);
    // for (int i = 0; i < num_partitions; i++) {
    //     printf("Partition %d: %ld\n", i, partition_lengths[i]);
    //     for (int j = 0; j < partition_lengths[i]; j++) {
    //         printf("    partitioning_key: %lld, payload: %lld\n", partitions[i][j].partitioning_key, partitions[i][j].payload);
    //     }
    // }
    // printf("\n\n");
    // pthread_mutex_unlock(&lock);

    for (int i = 0; i < num_partitions; i++)
        free(partitions[i]);
    free(partitions);
    free(partition_lengths);

    return NULL;
}

#endif
