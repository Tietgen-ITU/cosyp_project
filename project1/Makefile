build: $(wildcard src/*)
	gcc -o project1 src/*.c -Isrc -Wall -g

build-affinity: $(wildcard src/*)
	gcc -DWITH_CORE_AFFINITY=1 -o project1-ca src/*.c -Isrc -Wall -g

.PHONY: run
run: project1
	./project1 $(ARGS)
