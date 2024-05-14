#!/bin/bash

sizes=(1 2 4 8 16 32)
count=`expr ${#sizes[@]} - 1`
elastic_port=9200
psql_port=5049
# Run the benchmark

for i in $(seq 0 $count )
do :
    size=${sizes[i]}
    pport=`expr $psql_port + $i`
    eport=`expr $elastic_port + $i`
    echo "Elastic: ${eport}"
    # docker compose up "psql-${size}g elasic-${size}g" -d

    export COSYP_PSQL_CONNECTION_STRING="postgresql://cosyp-sa:123@localhost:${pport}/cosyp"
    export COSYP_ELASTIC_URL="http://localhost:${eport}"
    export BENCH_FOLDER_NAME="$(date +'%Y-%m-%d_%H-%M-%S')"
    # python3 benchmark.py
    # docker compose down "psql-${size}g elasic-${size}g"
done
