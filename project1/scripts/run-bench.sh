#!/bin/bash

set -e

timestamp=$(date +%s)

threads=(1 2 4 8 16 32)
hash_bits=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18)
tuples=(16777216)
algorithms=("independent" "concurrent")

mkdir -p bench-out
outfile="bench-out/bench-$timestamp.txt"

echo -e "repetition \t threads \t hash bits \t tuples \t algorithm \t time" | tee -a $outfile

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
          elapsed=$(./project1 -t $t -h $h -n $n -a $a | awk '/Elapsed: /{print $2 " " $3}')
          echo -e "$repetition \t $t \t $h \t $n \t \t $a \t $elapsed" | tee -a $outfile
        done
      done
    done
  done

  echo -ne "\n"
done

