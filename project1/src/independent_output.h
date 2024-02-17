#ifndef INDEPENDENT_OUTPUT
#define INDEPENDENT_OUTPUT

#include <stdio.h>
#include <pthread.h>
#include "partitioning_algorithm.h"

struct worker_args
{
    struct tuple *data;
    size_t length;
    int thread_num;
    int hash_bits;
};

void *worker(void *arguments);

void independent_output(struct partition_options *options)
{
    pthread_t *threads = malloc(options->num_threads * sizeof(pthread_t));
    pthread_attr_t *attr = malloc(options->num_threads * sizeof(pthread_attr_t));
    struct worker_args *args = malloc(options->num_threads * sizeof(struct worker_args));

    for (int i = 0; i < options->num_threads; i++)
    {
        // Assume data_length is divisible by num_threads
        size_t length = options->data_length / options->num_threads;
        struct tuple *data = options->data + (i * length);

        args[i] = (struct worker_args){
            .data = data,
            .length = length,
            .thread_num = i,
            .hash_bits = options->hash_bits};

        if (pthread_attr_init(&attr[i]))
        {
            printf("Error initialising thread attributes %d - aborting\n", i);
            goto cleanup;
        }

        if (pthread_create(&threads[i], &attr[i], worker, &args[i]))
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
}

void *worker(void *arguments)
{
    struct worker_args args = *((struct worker_args *)arguments);
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
