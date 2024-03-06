import matplotlib.pyplot as plt
from dataclasses import dataclass
import re
from itertools import groupby
import sys


@dataclass
class Configuration:
    avg_time: float | None
    repetitions: int
    threads: int
    hash_bits: int
    tuples: int
    algorithm: str
    binary: str

    def throughput(self):
        return self.tuples / (self.avg_time / 1000) / 1e6 if self.avg_time is not None else None


@dataclass
class Row:
    time: float | None
    repetition: int
    threads: int
    hash_bits: int
    tuples: int
    algorithm: str
    binary: str

    @staticmethod
    def from_line(line: str):
        line = re.sub(r'\s\s+', ' \t ', line)
        parts = [x.strip() for x in line.split('\t')]
        repetition, threads, hash_bits, tuples, binary, algorithm, time = parts

        return Row(
            time=int(time.split(" ")[0]) if time else None,
            repetition=int(repetition),
            threads=int(threads),
            hash_bits=int(hash_bits),
            tuples=int(tuples),
            algorithm=algorithm,
            binary=binary,
        )

    def configuration_key(self):
        return (self.threads, self.hash_bits, self.tuples, self.algorithm, self.binary)

    @staticmethod
    def averaged(rows: list['Row']):
        # Sanity check
        assert all(row.configuration_key() ==
                   rows[0].configuration_key() for row in rows)

        sum_time = 0
        num_times = 0
        for row in rows:
            if row.time is not None:
                sum_time += row.time
                num_times += 1
            else:
                print(f"Warning: Time is None for {row}")
        avg_time = sum_time / num_times if num_times > 0 else None

        return Configuration(
            avg_time=avg_time,
            repetitions=num_times,
            threads=rows[0].threads,
            hash_bits=rows[0].hash_bits,
            tuples=rows[0].tuples,
            algorithm=rows[0].algorithm,
            binary=rows[0].binary
        )


def read_data(filename):
    with open(filename) as f:
        lines = f.readlines()

    rows = [Row.from_line(line) for line in lines[1:]]

    scenario_reps = [list(g) for _, g in groupby(
        sorted(rows, key=lambda x: x.configuration_key()), lambda x: x.configuration_key())]

    configurations = [Row.averaged(reps) for reps in scenario_reps]

    algorithms = sorted(set(c.algorithm for c in configurations))
    groups = {a: [c for c in configurations if c.algorithm == a]
              for a in algorithms}

    y_max = max(t for t in (c.throughput() for c in configurations) if t is not None)

    for i, (group, configs) in enumerate(groups.items(), start=1):
        plt.subplot(1, len(groups), i)
        ax = plt.gca()

        configs = [c for c in configs if c.avg_time is not None and c.binary == "project1-ca"]
        configs.sort(key=lambda x: x.hash_bits)
        by_thread = {t: [c for c in configs if c.threads == t]
                     for t in sorted(set(c.threads for c in configs))}

        for threads, with_thread_num in by_thread.items():
            xs = [x.hash_bits for x in with_thread_num]
            ys = [x.throughput() for x in with_thread_num]
            plt.plot(xs, ys, '-o', label=f"{threads} threads")

        ax.set_xticks(sorted(set(c.hash_bits for c in configs)))
        plt.ylim(0, y_max * 1.05)
        plt.xlabel("Number of hash bits")
        plt.ylabel("Throughput (millions of tuples per second)")
        plt.title(group)
        plt.legend()

    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <file path>")
        exit(1)

    read_data(sys.argv[1])
