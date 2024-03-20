import matplotlib.pyplot as plt
from dataclasses import dataclass
import re
from itertools import groupby
import os
import sys
import numpy as np
import itertools


@dataclass
class Configuration:
    avg_time: float
    repetitions: int
    threads: int
    hash_bits: int
    tuples: int
    algorithm: str
    binary: str
    context_switches: int
    cpu_migrations: int
    dtlb_load_misses: int
    l1_dcache_load_misses: int
    llc_load_misses: int
    original_rows: list['Row']

    def throughput(self):
        return self.tuples / (self.avg_time / 1000) / 1e6 if self.avg_time is not None else None


@dataclass
class Row:
    time: float
    repetition: int
    threads: int
    hash_bits: int
    tuples: int
    algorithm: str
    binary: str
    context_switches: int
    cpu_migrations: int
    dtlb_load_misses: int
    l1_dcache_load_misses: int
    llc_load_misses: int

    @staticmethod
    def from_file(file: str):
        with open(file) as f:
            content = ''.join(f.readlines())

        command_params = re.search(
            r"\./(?P<binary>[-\w]+)"
            r" -t (?P<threads>\d+)"
            r" -h (?P<hash_bits>\d+)"
            r" -n (?P<tuples>\d+)"
            r" -a (?P<algorithm>\w+)", content).groupdict()

        def perf_metric(key): return int(
            re.search(r"(\d+)\s+"+key, content).group(1))

        return Row(
            time=int(re.search(r"Elapsed: (\d+) ms", content).group(1)),
            repetition=int(re.search(r"-r(\d+).txt", file).group(1)),
            threads=int(command_params["threads"]),
            hash_bits=int(command_params["hash_bits"]),
            tuples=int(command_params["tuples"]),
            algorithm=command_params["algorithm"],
            binary=command_params["binary"],
            context_switches=perf_metric("context-switches"),
            cpu_migrations=perf_metric("cpu-migrations"),
            dtlb_load_misses=perf_metric("dTLB-load-misses"),
            l1_dcache_load_misses=perf_metric("L1-dcache-load-misses"),
            llc_load_misses=perf_metric("LLC-load-misses"),
        )

    def configuration_key(self):
        return (self.threads, self.hash_bits, self.tuples, self.algorithm, self.binary)

    @staticmethod
    def averaged(rows: list['Row']):
        # Sanity check
        assert all(row.configuration_key() ==
                   rows[0].configuration_key() for row in rows)

        return Configuration(
            avg_time=sum(row.time for row in rows) / len(rows),
            context_switches=sum(
                row.context_switches for row in rows) / len(rows),
            cpu_migrations=sum(row.cpu_migrations for row in rows) / len(rows),
            dtlb_load_misses=sum(
                row.dtlb_load_misses for row in rows) / len(rows),
            l1_dcache_load_misses=sum(
                row.l1_dcache_load_misses for row in rows) / len(rows),
            llc_load_misses=sum(
                row.llc_load_misses for row in rows) / len(rows),
            repetitions=len(rows),
            threads=rows[0].threads,
            hash_bits=rows[0].hash_bits,
            tuples=rows[0].tuples,
            algorithm=rows[0].algorithm,
            binary=rows[0].binary,
            original_rows=rows,
        )

    def throughput(self):
        return self.tuples / (self.time / 1000) / 1e6 if self.time is not None else None


def read_data(folder):
    rows = []
    for entry in os.listdir(folder):
        row = Row.from_file(os.path.join(folder, entry))
        rows.append(row)

    print(f"Loaded {len(rows)} experiments")

    return rows


def plot_throughput(scenario_reps: list[list[Row]]):
    configurations = [Row.averaged(reps) for reps in scenario_reps]

    algorithms = sorted(set(c.algorithm for c in configurations))
    groups = {a: [c for c in configurations if c.algorithm == a]
              for a in algorithms}

    y_max = max(t for t in (c.throughput()
                for c in configurations) if t is not None)

    binary = "project1-ca"

    plt.figure(figsize=(13, 5))
    for i, (group, configs) in enumerate(groups.items(), start=1):
        plt.subplot(1, len(groups), i)
        ax = plt.gca()

        configs = [
            c for c in configs if c.avg_time is not None and c.binary == binary]
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

    with_ness = "without" if binary == "project1" else "with"
    plt.suptitle(
        f"Scaling of partitioning throughput with number of threads and hash bits ({with_ness} core affinity)")

    plt.savefig('plot.pdf', format="pdf", bbox_inches="tight")
    plt.show()


def plot_variance(scenario_reps: list[list[Row]]):
    configurations = [Row.averaged(reps) for reps in scenario_reps]

    algorithms = sorted(set(c.algorithm for c in configurations))
    groups = {a: [c for c in configurations if c.algorithm == a]
              for a in algorithms}

    y_max = max(t for t in (c.throughput()
                for c in configurations) if t is not None)

    binary = "project1"
    num_threads = 16

    plt.figure(figsize=(13, 5))
    for i, (group, configs) in enumerate(groups.items(), start=1):
        plt.subplot(1, len(groups), i)

        ax = plt.gca()

        configs = [
            c for c in configs if c.avg_time is not None and c.binary == binary]
        configs.sort(key=lambda x: x.hash_bits)
        by_thread = {t: [c for c in configs if c.threads == t]
                     for t in sorted(set(c.threads for c in configs))}

        with_thread_num = by_thread[num_threads]
        xs = [[r.throughput() for r in x.original_rows]
              for x in with_thread_num]
        labels = [x.hash_bits for x in with_thread_num]

        plt.boxplot(xs, labels=labels)  # ys, '-o', label=f"{threads} threads"

        ax.set_xticks(sorted(set(c.hash_bits for c in configs)))
        plt.ylim(0, y_max)
        plt.xlabel("Number of hash bits")
        plt.ylabel("Throughput (millions of tuples per second)")
        plt.title(group)
        plt.legend()

    with_ness = "without" if binary == "project1" else "with"
    plt.suptitle(
        f"Throughput variance {with_ness} core affinity ({num_threads} threads)")
    plt.savefig('plot.png', transparent=True)
    plt.show()


def plot_perf_stuff(scenario_reps: list[list[Row]]):
    configurations = [Row.averaged(reps) for reps in scenario_reps]

    algorithms = sorted(set(c.algorithm for c in configurations))
    groups = {a: [c for c in configurations if c.algorithm == a]
              for a in algorithms}

    metric_labels = {
        "context_switches": "context switches",
        "cpu_migrations": "CPU migrations",
        "dtlb_load_misses": "dTLB load misses",
        "l1_dcache_load_misses": "L1 dcache load misses",
        "llc_load_misses": "LLC load misses",
    }

    binaries = ["project1", "project1-ca"]
    metrics = list(metric_labels.keys())
    combinations = [(x, y) for x in binaries for y in metrics]

    for binary, metric in combinations:
        y_max = max(t for t in (getattr(c, metric)
                                for c in configurations) if t is not None)

        plt.figure(figsize=(13, 5))
        for i, (group, configs) in enumerate(groups.items(), start=1):
            plt.subplot(1, len(groups), i)
            ax = plt.gca()

            configs = [
                c for c in configs if c.avg_time is not None and c.binary == binary]
            configs.sort(key=lambda x: x.hash_bits)
            by_thread = {t: [c for c in configs if c.threads == t]
                         for t in sorted(set(c.threads for c in configs))}

            for threads, with_thread_num in by_thread.items():
                xs = [x.hash_bits for x in with_thread_num]
                ys = [getattr(x, metric) for x in with_thread_num]
                plt.plot(xs, ys, '-o', label=f"{threads} threads")

            ax.set_xticks(sorted(set(c.hash_bits for c in configs)))
            plt.ylim(0, y_max)
            plt.xlabel("Number of hash bits")
            plt.ylabel(f"Number of {metric_labels[metric]}")
            plt.title(group)
            plt.legend()
            # plt.yscale("log", base=10)
            # plt.yticks(10 ** np.arange(7, 7.5, 0.5))

        with_ness = "without" if binary == "project1" else "with"
        plt.suptitle(
            f"Scaling of {metric_labels[metric]} with number of threads and hash bits ({with_ness} core affinity)")

        format = "png"
        name = f"{metric}_{binary}.{format}"
        plt.savefig(f"plot_out/{name}", format=format, bbox_inches="tight")
        # plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <file path>")
        exit(1)

    measurements = read_data(sys.argv[1])

    scenario_reps = [list(g) for _, g in groupby(
        sorted(measurements, key=lambda x: x.configuration_key()), lambda x: x.configuration_key())]

    plot_perf_stuff(scenario_reps)
