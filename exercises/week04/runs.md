## `caching-0`

```text
$ ./caching-0
Testing up to array of size 8000
clockspersec 1000000Testing for array of size 10 * 10 = 100
Horizontal took 0.000941 cpu seconds
Vertical took 0.000759 cpu seconds

Testing for array of size 260 * 260 = 67600
Horizontal took 0.291729 cpu seconds
Vertical took 0.271866 cpu seconds

Testing for array of size 510 * 510 = 260100
Horizontal took 1.085344 cpu seconds
Vertical took 1.040763 cpu seconds

Testing for array of size 760 * 760 = 577600
Horizontal took 2.405416 cpu seconds
Vertical took 2.307385 cpu seconds

Testing for array of size 1010 * 1010 = 1020100
Horizontal took 4.246441 cpu seconds
Vertical took 4.071477 cpu seconds

Testing for array of size 1260 * 1260 = 1587600
Horizontal took 6.607251 cpu seconds
Vertical took 6.331907 cpu seconds

Testing for array of size 1510 * 1510 = 2280100
Horizontal took 9.482616 cpu seconds
Vertical took 10.990712 cpu seconds

Testing for array of size 1760 * 1760 = 3097600
Horizontal took 12.876795 cpu seconds
Vertical took 18.229197 cpu seconds

Testing for array of size 2010 * 2010 = 4040100
Horizontal took 16.795776 cpu seconds
Vertical took 29.823822 cpu seconds

Testing for array of size 2260 * 2260 = 5107600
Horizontal took 21.210429 cpu seconds
Vertical took 38.406750 cpu seconds

Testing for array of size 2510 * 2510 = 6300100
Horizontal took 26.182139 cpu seconds
Vertical took 47.067957 cpu seconds

Testing for array of size 2760 * 2760 = 7617600
Horizontal took 31.648829 cpu seconds
Vertical took 59.408590 cpu seconds

Testing for array of size 3010 * 3010 = 9060100
Horizontal took 37.646395 cpu seconds
Vertical took 72.475848 cpu seconds

Testing for array of size 3260 * 3260 = 10627600
Horizontal took 44.167651 cpu seconds
Vertical took 86.387713 cpu seconds

Testing for array of size 3510 * 3510 = 12320100
Horizontal took 51.199541 cpu seconds
Vertical took 104.310881 cpu seconds

<stopped it here, didn't have time to wait>
```

## Using `perf` to compare horizontal and vertical

### `horizontal-0`

```text
$ perf stat -e cycles,instructions,L1-icache-load-misses,L1-dcache-load-misses,LLC-load-misses,cache-misses,uops_retired.stall_cycles,branch-misses,iTLB-load-misses,dTLB-load-misses ./horizontal-0

Testing up to array of size 8000
Testing for array of size 10 * 10 = 100
Horisontal took 0.000821 cpu milliseconds
Testing for array of size 260 * 260 = 67600
Horisontal took 0.292365 cpu milliseconds
Testing for array of size 510 * 510 = 260100
Horisontal took 1.087722 cpu milliseconds
Testing for array of size 760 * 760 = 577600
Horisontal took 2.410373 cpu milliseconds
Testing for array of size 1010 * 1010 = 1020100
Horisontal took 4.254531 cpu milliseconds
Testing for array of size 1260 * 1260 = 1587600
Horisontal took 6.619344 cpu milliseconds
Testing for array of size 1510 * 1510 = 2280100
Horisontal took 9.500610 cpu milliseconds
Testing for array of size 1760 * 1760 = 3097600
Horisontal took 12.902032 cpu milliseconds
Testing for array of size 2010 * 2010 = 4040100
Horisontal took 16.828063 cpu milliseconds
Testing for array of size 2260 * 2260 = 5107600
Horisontal took 21.260270 cpu milliseconds
Testing for array of size 2510 * 2510 = 6300100
^C./horizontal-0: Interrupt

 Performance counter stats for './horizontal-0':

      159474501536      cycles                                                                  (50.00%)
      365370879479      instructions                     #    2.29  insn per cycle              (60.00%)
          10090178      L1-icache-load-misses                                                   (60.00%)
           9461743      L1-dcache-load-misses                                                   (60.00%)
             91495      LLC-load-misses                                                         (60.00%)
            427192      cache-misses                                                            (60.00%)
       48862192736      uops_retired.stall_cycles                                               (40.00%)
          12302480      branch-misses                                                           (40.00%)
             89532      iTLB-load-misses                                                        (40.00%)
            911817      dTLB-load-misses                                                        (40.00%)

      80.087709845 seconds time elapsed

      80.019873000 seconds user
       0.063996000 seconds sys
```

### `vertical-0`

```text
$ perf stat -e cycles,instructions,L1-icache-load-misses,L1-dcache-load-misses,LLC-load-misses,cache-misses,uops_retired.stall_cycles,branch-misses,iTLB-load-misses,dTLB-load-misses ./vertical-0

Testing up to array of size 8000
Testing for array of size 10 * 10 = 100
Vertical took 0.000550 cpu milliseconds

Testing for array of size 260 * 260 = 67600
Vertical took 0.284037 cpu milliseconds

Testing for array of size 510 * 510 = 260100
Vertical took 1.055097 cpu milliseconds

Testing for array of size 760 * 760 = 577600
Vertical took 2.338421 cpu milliseconds

Testing for array of size 1010 * 1010 = 1020100
Vertical took 4.127445 cpu milliseconds

Testing for array of size 1260 * 1260 = 1587600
Vertical took 6.422335 cpu milliseconds

Testing for array of size 1510 * 1510 = 2280100
Vertical took 11.010304 cpu milliseconds

Testing for array of size 1760 * 1760 = 3097600
Vertical took 18.435797 cpu milliseconds

Testing for array of size 2010 * 2010 = 4040100
Vertical took 29.920091 cpu milliseconds

Testing for array of size 2260 * 2260 = 5107600
Vertical took 38.614276 cpu milliseconds

Testing for array of size 2510 * 2510 = 6300100
^C./vertical-0: Interrupt

 Performance counter stats for './vertical-0':

      226062999998      cycles                                                                  (50.00%)
      346288060445      instructions                     #    1.53  insn per cycle              (60.00%)
          13964006      L1-icache-load-misses                                                   (60.00%)
        6432277218      L1-dcache-load-misses                                                   (60.00%)
            314017      LLC-load-misses                                                         (60.00%)
           1162275      cache-misses                                                            (60.00%)
      129655742826      uops_retired.stall_cycles                                               (40.00%)
          12083565      branch-misses                                                           (40.00%)
             69797      iTLB-load-misses                                                        (40.00%)
       12863857113      dTLB-load-misses                                                        (40.00%)

     113.530042353 seconds time elapsed

     113.485511000 seconds user
       0.039999000 seconds sys
```

### Comparison

```
Horizontal:
      159474501536      cycles                                                                  (50.00%)
      365370879479      instructions                     #    2.29  insn per cycle              (60.00%)
          10090178      L1-icache-load-misses                                                   (60.00%)
           9461743      L1-dcache-load-misses                                                   (60.00%)
             91495      LLC-load-misses                                                         (60.00%)
            427192      cache-misses                                                            (60.00%)
       48862192736      uops_retired.stall_cycles                                               (40.00%)
          12302480      branch-misses                                                           (40.00%)
             89532      iTLB-load-misses                                                        (40.00%)
            911817      dTLB-load-misses                                                        (40.00%)

Vertical:
      226062999998      cycles                                                                  (50.00%)
      346288060445      instructions                     #    1.53  insn per cycle              (60.00%)
          13964006      L1-icache-load-misses                                                   (60.00%)
        6432277218      L1-dcache-load-misses                                                   (60.00%)
            314017      LLC-load-misses                                                         (60.00%)
           1162275      cache-misses                                                            (60.00%)
      129655742826      uops_retired.stall_cycles                                               (40.00%)
          12083565      branch-misses                                                           (40.00%)
             69797      iTLB-load-misses                                                        (40.00%)
       12863857113      dTLB-load-misses                                                        (40.00%)
```

Vertical has VASTLY more L1-dcache-load-misses and dTLB-load-misses

## Varying optimisation level

### `horizontal-3`

```text
$ perf stat -e cycles,instructions,L1-icache-load-misses,L1-dcache-load-misses,LLC-load-misses,cache-misses,uops_retired.stall_cycles,branch-misses,iTLB-load-misses,dTLB-load-misses ./horizontal-3

Testing up to array of size 8000
Testing for array of size 10 * 10 = 100
Horisontal took 0.000182 cpu milliseconds
Testing for array of size 260 * 260 = 67600
Horisontal took 0.098673 cpu milliseconds
Testing for array of size 510 * 510 = 260100
Horisontal took 0.304039 cpu milliseconds
Testing for array of size 760 * 760 = 577600
Horisontal took 0.674834 cpu milliseconds
Testing for array of size 1010 * 1010 = 1020100
Horisontal took 1.191591 cpu milliseconds
Testing for array of size 1260 * 1260 = 1587600
Horisontal took 1.853940 cpu milliseconds
Testing for array of size 1510 * 1510 = 2280100
Horisontal took 2.662236 cpu milliseconds
Testing for array of size 1760 * 1760 = 3097600
Horisontal took 3.616191 cpu milliseconds
Testing for array of size 2010 * 2010 = 4040100
Horisontal took 4.716137 cpu milliseconds
Testing for array of size 2260 * 2260 = 5107600
Horisontal took 5.962081 cpu milliseconds
Testing for array of size 2510 * 2510 = 6300100
^C./horizontal-3: Interrupt

 Performance counter stats for './horizontal-3':

       43357877383      cycles                                                                  (49.98%)
      130624377845      instructions                     #    3.01  insn per cycle              (59.98%)
           2960890      L1-icache-load-misses                                                   (59.98%)
           5976975      L1-dcache-load-misses                                                   (59.98%)
             19761      LLC-load-misses                                                         (60.00%)
             91706      cache-misses                                                            (60.02%)
        7745721041      uops_retired.stall_cycles                                               (40.02%)
          11715175      branch-misses                                                           (40.02%)
             51515      iTLB-load-misses                                                        (40.00%)
            536457      dTLB-load-misses                                                        (39.98%)

      21.792080914 seconds time elapsed

      21.730519000 seconds user
       0.059984000 seconds sys
```

### `vertical-3`

```text
$ perf stat -e cycles,instructions,L1-icache-load-misses,L1-dcache-load-misses,LLC-load-misses,cache-misses,uops_retired.stall_cycles,branch-misses,iTLB-load-misses,dTLB-load-misses ./vertical-3

Testing up to array of size 8000
Testing for array of size 10 * 10 = 100
Vertical took 0.000523 cpu milliseconds

Testing for array of size 260 * 260 = 67600
Vertical took 0.156167 cpu milliseconds

Testing for array of size 510 * 510 = 260100
Vertical took 0.530519 cpu milliseconds

Testing for array of size 760 * 760 = 577600
Vertical took 1.173368 cpu milliseconds

Testing for array of size 1010 * 1010 = 1020100
Vertical took 2.068280 cpu milliseconds

Testing for array of size 1260 * 1260 = 1587600
Vertical took 3.214869 cpu milliseconds

Testing for array of size 1510 * 1510 = 2280100
Vertical took 8.739743 cpu milliseconds

Testing for array of size 1760 * 1760 = 3097600
Vertical took 17.757032 cpu milliseconds

Testing for array of size 2010 * 2010 = 4040100
Vertical took 30.378658 cpu milliseconds

Testing for array of size 2260 * 2260 = 5107600
Vertical took 39.084631 cpu milliseconds

Testing for array of size 2510 * 2510 = 6300100
^C./vertical-3: Interrupt

 Performance counter stats for './vertical-3':

      229209070113      cycles                                                                  (50.00%)
      157211724632      instructions                     #    0.69  insn per cycle              (60.00%)
          14743703      L1-icache-load-misses                                                   (60.00%)
        7180535579      L1-dcache-load-misses                                                   (60.00%)
            170246      LLC-load-misses                                                         (60.00%)
            695440      cache-misses                                                            (60.00%)
      177489713547      uops_retired.stall_cycles                                               (40.00%)
          12663877      branch-misses                                                           (40.00%)
            100885      iTLB-load-misses                                                        (40.00%)
       14163224876      dTLB-load-misses                                                        (40.00%)

     115.118864422 seconds time elapsed

     115.068309000 seconds user
       0.043998000 seconds sys
```

### Comparison

- Vertical still bad
- Horizontal much faster
- Horizontal has fewer overall instructions
- Horizontal has fewer cache misses

## Unrolling

TBA. Hypothesis: unrolling up to approx 4 is going to be great, after that probably not so much
