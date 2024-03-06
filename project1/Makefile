build: $(wildcard src/*)
	gcc -o project1 src/*.c -Isrc -Wall -g -O3

build-affinity: $(wildcard src/*)
	gcc -DWITH_CORE_AFFINITY=1 -D_GNU_SOURCE -o project1-ca src/*.c -Isrc -Wall -g -O3

.PHONY: run
run: project1
	./project1 $(ARGS)
