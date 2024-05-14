#!/bin/bash

sizes=(1 2 4 8)
count=`expr ${#sizes[@]} - 1`
elastic_port=9200
psql_port=5049

export BENCH_FOLDER_NAME="$(date +'%Y-%m-%d_%H-%M-%S')"

# Run the benchmark
for i in $(seq 0 $count )
do :
    size=${sizes[i]}
    pport=`expr $psql_port + $i`
    eport=`expr $elastic_port + $i`
    export COSYP_PSQL_CONNECTION_STRING="postgresql://cosyp-sa:123@localhost:${pport}/cosyp"
    export COSYP_ELASTIC_URL="http://localhost:${eport}"
    export DATASET_SIZE_GB="$size"

    docker compose start "psql-${size}g"
    docker compose start "elastic-${size}g"
    python3 benchmark.py
    docker compose stop "psql-${size}g"
    docker compose stop "elastic-${size}g"
done
