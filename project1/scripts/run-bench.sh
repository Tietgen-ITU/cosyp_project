#!/bin/bash

set -e

timestamp=$(date +%s)

threads=(1 2 4 8 16 32)
hash_bits=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18)
tuples=(16777216)
algorithms=("independent" "concurrent")
binaries=("project1" "project1-ca")

perf_events="context-switches,cpu-migrations,dTLB-load-misses,L1-dcache-load-misses,LLC-load-misses"

outdir="bench-out/bench-$timestamp"
mkdir -p $outdir

for repetition in {1..8}
do :
  for t in "${threads[@]}"
  do :
    for h in "${hash_bits[@]}"
    do :
      for n in "${tuples[@]}"
      do :
        for a in "${algorithms[@]}"
        do :
          for binary in "${binaries[@]}"
          do :
            run_command="./$binary -t $t -h $h -n $n -a $a"

            now=$(date +"%Y-%m-%d %H:%M:%S")
            echo -e "[$now] benching $run_command"

            outfile="bench-$a-t$t-h$h-n$n-$binary-r$repetition.txt"
            perf stat -e $perf_events $run_command &> "$outdir/$outfile"

            now=$(date +"%Y-%m-%d %H:%M:%S")
            echo -e "[$now] finished (wrote to $outfile)"
          done
        done
      done
    done
  done
done
