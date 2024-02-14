Same-core:

```
group101@dionysos:~/exercises/week03/code-examples3$ ./a.out 2 20 20
Example usage:
./affinitynumaexample 4 0 8 16 24
Starting number of threads: 2
CPU: 20
CPU: 20
Counter value: 200000
Duration: 20814 microseconds
```

Different cores on same machine, huge difference:

```
group101@dionysos:~/exercises/week03/code-examples3$ ./a.out 2 20 22
Example usage:
./affinitynumaexample 4 0 8 16 24
Starting number of threads: 2
CPU: 20
CPU: 22
Counter value: 200000
Duration: 55018 microseconds
```

Different cores on same NUMA node:

```
group101@dionysos:~/exercises/week03/code-examples3$ ./a.out 6 20 22 24 26 28 30
Example usage:
./affinitynumaexample 4 0 8 16 24
Starting number of threads: 6
CPU: 20
CPU: 22
CPU: 24
CPU: 26
CPU: 28
CPU: 30
Counter value: 600000
Duration: 160291 microseconds
```

Different cores on different NUMA nodes:

```
group101@dionysos:~/exercises/week03/code-examples3$ ./a.out 6 20 22 23 25 24 27
Example usage:
./affinitynumaexample 4 0 8 16 24
Starting number of threads: 6
CPU: 20
CPU: 22
CPU: 23
CPU: 25
CPU: 24
CPU: 27
Counter value: 600000
Duration: 205088 microseconds
```
