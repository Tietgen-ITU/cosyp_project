#ifndef INDEPENDENT_OUTPUT
#define INDEPENDENT_OUTPUT

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include "hash.h"
#include "partitioning_algorithm.h"

struct independent_output_worker_args
{
    struct tuple *data;
    size_t length;
    int thread_num;
    int hash_bits;
    size_t *partition_lengths;
    struct tuple **partitions;
};

void *independent_output_worker(void *arguments);

void independent_output(struct partition_options *options)
{
    pthread_t *threads = (pthread_t *)malloc(options->num_threads * sizeof(pthread_t));
    pthread_attr_t *attr = (pthread_attr_t *)malloc(options->num_threads * sizeof(pthread_attr_t));
    struct independent_output_worker_args *args = (struct independent_output_worker_args *)malloc(options->num_threads * sizeof(struct independent_output_worker_args));

    size_t num_allocated_partitions = 0;
    size_t **all_partition_lengths = (size_t **)malloc(options->num_threads * sizeof(size_t *));
    struct tuple ***all_partitions = (struct tuple ***)malloc(options->num_threads * sizeof(struct tuple **));

    size_t num_partitions = (1 << options->hash_bits);

    for (int i = 0; i < options->num_threads; i++)
    {
        num_allocated_partitions++;

        // Assume data_length is divisible by num_threads
        size_t length = options->data_length / options->num_threads;
        struct tuple *data = options->data + (i * length);

        size_t expected_size = length / num_partitions;

        // TODO: re-evaluate. 4x to minimise probability of exceeding buffer size.
        // Could do wrap-around and overwrite previous entries? But this is wrong.
        size_t partition_space = expected_size * 4;

        size_t *partition_lengths = (size_t *)malloc(num_partitions * sizeof(size_t));
        struct tuple **partitions = (struct tuple **)malloc(num_partitions * sizeof(struct tuple *));
        for (int i = 0; i < num_partitions; i++)
        {
            partitions[i] = (struct tuple *)malloc(partition_space * sizeof(struct tuple));
            partition_lengths[i] = 0;
        }

        all_partition_lengths[i] = partition_lengths;
        all_partitions[i] = partitions;

        args[i] = (struct independent_output_worker_args){
            .data = data,
            .length = length,
            .thread_num = i,
            .hash_bits = options->hash_bits,
            .partition_lengths = partition_lengths,
            .partitions = partitions};
    }

    for (int i = 0; i < options->num_threads; i++)
    {
        if (pthread_attr_init(&attr[i]))
        {
            printf("Error initialising thread attributes %d - aborting\n", i);
            goto cleanup;
        }

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
    for (int i = 0; i < num_allocated_partitions; i++)
    {
        for (int j = 0; j < num_partitions; j++)
        {
            free(all_partitions[i][j]);
        }
        free(all_partitions[i]);
        free(all_partition_lengths[i]);
    }
    free(all_partitions);
    free(all_partition_lengths);

    free(threads);
    free(attr);
    free(args);
}

void *independent_output_worker(void *arguments)
{
    struct independent_output_worker_args args = *(struct independent_output_worker_args *)arguments;

    for (size_t i = 0; i < args.length; i++)
    {
        int64_t partition_index = hash(args.data[i].partitioning_key, args.hash_bits);
        size_t cur_partition_length = args.partition_lengths[partition_index];
        args.partitions[partition_index][cur_partition_length] = args.data[i];
        args.partition_lengths[partition_index]++;
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

    return NULL;
}

#endif
