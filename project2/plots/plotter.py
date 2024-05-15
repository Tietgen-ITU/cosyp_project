from matplotlib.axes import mticker
import matplotlib.pyplot as plt
from dataclasses import dataclass
import os
import sys
import json
import matplotlib as mpl
from numpy import average
import numpy as np
import copy
import hashlib

mpl.rcParams['figure.dpi'] = 600


strategies = ["batch", "single"]
runners = ["postgres", "elasticsearch"]
query_types = ["in_many_articles", "in_few_articles", "random", "no_matches"]
dataset_sizes = ["1", "2", "4", "8", "16", "32"]

QT_LABELS = {
    "in_many_articles": "Abundant queries",
    "in_few_articles": "Sparse queries",
    "random": "Random queries",
    "no_matches": "No-hit queries"
}

RUNNER_LABELS = {
    "postgres": "Postgres",
    "elasticsearch": "Elasticsearch"
}

STRATEGY_LABELS = {
    "batch": "Batch",
    "single": "Sequential"
}

@dataclass
class Configuration:
    data: dict

    @staticmethod
    def from_file(file):
        with open(file, "r") as f:
            data = json.load(f)
            return Configuration(data)

    def config(self):
        return self.data["configuration"]

    def latencies(self, runner: str):
        return [q["elapsed_ms"] for q in self.data["runners"][runner]["queries"]]

    def metrics(self, runner: str):
        all_latencies = self.latencies(runner)
        n = self.config()["num_queries"]
        avg_latency = sum(all_latencies) / len(all_latencies)
        percentile_99 = sorted(all_latencies)[int(len(all_latencies) * 0.99)]
        percentile_1 = sorted(all_latencies)[int(len(all_latencies) * 0.01)]
        throughput = n / \
            (self.data["runners"][runner]["total_elapsed_ms"] / 1000)
        return Metrics(avg_latency, percentile_99, percentile_1, throughput)

    def resource_usage(self, runner: str):
        return self.data["runners"][runner]["stats"]


@dataclass
class Metrics:
    avg_latency: float
    percentile_99: float
    percentile_1: float
    throughput: float


def save_plot(name):
    format = "png"
    plt.savefig(f"plot_out/{format}/{name}.{format}",
                format=format, bbox_inches="tight")
    plt.close()


MARKERS = [('*', None), ('s', None), ('o', None),
           ('x', None), ('|', None), ('s', 'none')]


def read_data(folder):
    configs = []

    for filename in os.listdir(folder):
        file = os.path.join(folder, filename)
        config = Configuration.from_file(file)
        configs.append(config)

    print(f"Loaded {len(configs)} experiments")

    return configs


def plot_throughput(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations = [c for c in configurations if c.config()["dataset_size_gb"] == "1"]
    configurations.sort(key=lambda x: x.config()["num_words"])

    for strategy in strategies:
        for qt in query_types:
            plt.figure(figsize=(13, 5))

            for i, runner in enumerate(runners):
                confs = [c for c in configurations if c.config(
                )["strategy"] == strategy and c.config()["query_type"] == qt]

                xs = [c.config()["num_words"][0] for c in confs]
                ys = [c.metrics(runner).throughput for c in confs]
                marker, facecolor = MARKERS[i]

                plt.plot(xs, ys, f'-{marker}',
                         markerfacecolor=facecolor, label=RUNNER_LABELS[runner])

            ax = plt.gca()
            ax.set_xscale('log', base=2)
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

            plt.xlabel("Number of words in query")
            plt.ylabel("Throughput (queries/second)")
            plt.grid()
            plt.title(
                f"Throughput for different query sizes ({STRATEGY_LABELS[strategy].lower()}, {QT_LABELS[qt].lower()})")
            plt.legend()

            save_plot(f"throughput-{strategy}-{qt}")


def plot_throughput_per_query_type(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations = [c for c in configurations if c.config()["dataset_size_gb"] == "1"]
    configurations.sort(key=lambda x: x.config()["num_words"])

    for strategy in strategies:
        min_y, max_y = 0, 0

        plt.figure(figsize=(13, 5))
        for i, runner in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)

            for j, qt in enumerate(query_types):
                confs = [c for c in configurations if c.config(
                )["strategy"] == strategy and c.config()["query_type"] == qt]

                xs = [c.config()["num_words"][0] for c in confs]
                ys = [c.metrics(runner).throughput for c in confs]
                marker, facecolor = MARKERS[j]

                min_y = min(min_y, min(ys))
                max_y = max(max_y, max(ys))

                plt.plot(xs, ys, f'-{marker}',
                         markerfacecolor=facecolor, label=f"{QT_LABELS[qt]}")

            ax = plt.gca()
            ax.set_xscale('log', base=2)
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

            plt.xlabel("Number of words in query")
            plt.ylabel("Throughput (queries/second)")
            plt.grid()
            plt.title(RUNNER_LABELS[runner])
            plt.legend()

        for i, _ in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)
            plt.ylim(0, max_y * 1.1)

        plt.suptitle(f"Throughput for different query types ({STRATEGY_LABELS[strategy].lower()})")

        save_plot(f"throughput-query-cardinality-{strategy}")


def plot_throughput_per_strategy(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations = [c for c in configurations if c.config()["dataset_size_gb"] == "1"]
    configurations.sort(key=lambda x: x.config()["num_words"])

    for qt in query_types:
        min_y, max_y = 0, 0

        plt.figure(figsize=(13, 5))
        for i, runner in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)

            for j, strategy in enumerate(strategies):
                confs = [c for c in configurations if c.config(
                )["strategy"] == strategy and c.config()["query_type"] == qt]

                xs = [c.config()["num_words"][0] for c in confs]
                ys = [c.metrics(runner).throughput for c in confs]
                marker, facecolor = MARKERS[j]

                min_y = min(min_y, min(ys))
                max_y = max(max_y, max(ys))

                plt.plot(xs, ys, f'-{marker}',
                         markerfacecolor=facecolor, label=f"{STRATEGY_LABELS[strategy].lower()}")

            ax = plt.gca()
            ax.set_xscale('log', base=2)
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

            plt.xlabel("Number of words in query")
            plt.ylabel("Throughput (queries/second)")
            plt.grid()
            plt.title(RUNNER_LABELS[runner])
            plt.legend()

        for i, _ in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)
            plt.ylim(0, max_y * 1.1)

        plt.suptitle(f"Throughput for different query strategies ({QT_LABELS[qt].lower()})")

        save_plot(f"throughput-query-strategy-{qt}")




def plot_variance(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations = [c for c in configurations if c.config()["dataset_size_gb"] == "1"]
    configurations.sort(key=lambda x: x.config()["num_words"])

    for strategy in strategies:
        for qt in query_types:
            plt.figure(figsize=(13, 5))

            for i, runner in enumerate(runners):
                plt.subplot(1, len(runners), i + 1)

                confs = [c for c in configurations if c.config()["strategy"]
                         == strategy and c.config()["query_type"] == qt]

                if not len(confs):
                    continue

                xs = [c.config()["num_words"][0] for c in confs]
                ys = [c.latencies(runner) for c in confs]

                plt.boxplot(ys, labels=xs, showmeans=True)

                plt.title(f"Latencies for {runner} ({STRATEGY_LABELS[strategy].lower()}, {QT_LABELS[qt].lower()})")
                plt.xlabel("Number of words in query")
                plt.ylabel("Latency (ms)")
                plt.grid()

            save_plot(f"variance-{strategy}-{qt}")


def plot_resource_usage(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations = [c for c in configurations if c.config()["dataset_size_gb"] == "1"]
    configurations.sort(key=lambda x: x.config()["num_words"])

    for qt in query_types:
        plt.figure(figsize=(13, 5))
        max_perc = 400 # 0
        for i, runner in enumerate(runners):
            for j, strategy in enumerate(strategies):
                plt.subplot(1, len(runners), i + 1)

                confs = [c for c in configurations if c.config(
                )["strategy"] == strategy and c.config()["query_type"] == qt]

                xs, ys = [], []
                marker, facecolor = MARKERS[j]
                for c in confs:
                    x = c.config()["num_words"][0]
                    percs = [stat["cpu_perc"]
                             for stat in c.resource_usage(runner)]

                    if len(percs) == 0:
                        continue

                    xs.append(x)
                    y = average(percs)
                    ys.append(y)

                    # max_percs = [stat["cpu_max_perc"]
                    #              for stat in c.resource_usage(runner)]
                    # max_perc = max(max_perc, max(max_percs))

                plt.plot(xs, ys, f'-{marker}',
                         markerfacecolor=facecolor, label=f"{STRATEGY_LABELS[strategy]}")

                ax = plt.gca()
                ax.set_xscale('log', base=2)
                ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

                plt.title(RUNNER_LABELS[runner])
                plt.xlabel("Number of words in query")
                plt.ylabel(f"CPU usage (%)")
                plt.grid()

        for i, _ in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)
            plt.axhline(y=max_perc, color='r', linestyle='--',
                        label='Maximum possible cpu usage')
            plt.ylim(0, max_perc * 1.1)
            plt.legend()

        plt.suptitle(f"CPU usage for different query strategies ({QT_LABELS[qt].lower()})")

        save_plot(f"resource-usage-{qt}")


def plot_latencies(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations = [c for c in configurations if c.config()["dataset_size_gb"] == "1" and c.config()["strategy"] == "single"]
    configurations.sort(key=lambda x: x.config()["num_words"])

    charts = [
        {
            "title": "Average",
            "key": "avg_latency",
        },
        {
            "title": "99th percentile",
            "key": "percentile_99",
        },
        {
            "title": "1st percentile",
            "key": "percentile_1",
        },
    ]

    for chart in charts:
        plt.figure(figsize=(13, 5))

        max_y = 0
        for i, runner in enumerate(runners):
            ax = plt.subplot(1, len(runners), i + 1)
            ax.grid()

            for j, qt in enumerate(query_types):
                confs = [c for c in configurations if c.config()["query_type"] == qt]

                bar_positions = list(range(len(confs)))
                xs = [x for x in bar_positions]
                ys = np.array([getattr(c.metrics(runner), chart["key"]) for c in confs])

                marker, facecolor = MARKERS[j]
                ax.plot(xs, ys, f'-{marker}', markerfacecolor=facecolor, label=QT_LABELS[qt])
                max_y = max(max_y, max(ys))

                ax.set_xticks(bar_positions, [c.config()["num_words"][0] for c in confs])

            ax.grid(zorder=0)

        for i, runner in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)
            plt.ylim(0, max_y * 1.05)
            plt.xlabel("Number of words in query")
            plt.ylabel("Latency (ms)")
            plt.title(RUNNER_LABELS[runner])
            plt.legend()

        plt.suptitle(f"{chart['title']} latency for different query sizes")

        save_plot(f"latency-{chart['key']}")


def plot_throughput_per_dataset_size(configurations: list[Configuration]):
    configurations = [g["combined"] for g in group_by_repetition(configurations)]
    configurations.sort(key=lambda x: x.config()["num_words"])
    query_type = "random"

    for strategy in strategies:
        min_y, max_y = 0, 0

        plt.figure(figsize=(13, 5))
        for i, runner in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)

            for j, dataset_size in enumerate(dataset_sizes):
                confs = [c for c in configurations if c.config()["strategy"] == strategy and c.config()["query_type"] == query_type and c.config()["dataset_size_gb"] == dataset_size]

                if not len(confs):
                    continue

                xs = [c.config()["num_words"][0] for c in confs]
                ys = [c.metrics(runner).throughput for c in confs]
                marker, facecolor = MARKERS[j]

                min_y = min(min_y, min(ys))
                max_y = max(max_y, max(ys))

                plt.plot(xs, ys, f'-{marker}',
                         markerfacecolor=facecolor, label=f"{dataset_size} GB")

            ax = plt.gca()
            ax.set_xscale('log', base=2)
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

            plt.xlabel("Number of words in query")
            plt.ylabel("Throughput (queries/second)")
            plt.grid()
            plt.title(RUNNER_LABELS[runner])
            plt.legend()

        for i, _ in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)
            plt.ylim(0, max_y * 1.1)

        plt.suptitle(f"Throughput for different dataset sizes ({STRATEGY_LABELS[strategy].lower()}, {QT_LABELS[query_type].lower()})")

        save_plot(f"throughput-dataset-size-{strategy}")


def group_by_repetition(configurations: list[Configuration]):
    groups = {}

    for c in configurations:
        cc = copy.deepcopy(c.config())
        cc.pop("repetition")
        cc.pop("seed")
        hashable = json.dumps(sorted((k, str(v)) for k,v in cc.items()))
        configuration_hash = hashlib.md5(hashable.encode()).hexdigest()

        if configuration_hash not in groups:
            groups[configuration_hash] = {
                "combined": Configuration(copy.deepcopy(c.data)),
                "sources": [c]
            }
            groups[configuration_hash]["combined"].data["configuration"] = cc
        else:
            write_to = groups[configuration_hash]["combined"].data
            groups[configuration_hash]["sources"].append(c)

            for runner, val in c.data["runners"].items():
                write_to["runners"][runner]["queries"].extend(val["queries"])
                write_to["runners"][runner]["total_elapsed_ms"] += val["total_elapsed_ms"]
                write_to["runners"][runner]["stats"].extend(val["stats"])

    return groups.values()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <dir path>")
        exit(1)

    configurations = read_data(sys.argv[1])

    for c in configurations:
        print(c.config())

    print("Plotting throughput...")
    plot_throughput(configurations)
    print("Plotting throughput per query type...")
    plot_throughput_per_query_type(configurations)
    print("Plotting variance...")
    plot_variance(configurations)
    print("Plotting resource usage...")
    plot_resource_usage(configurations)
    print("Plotting latencies...")
    plot_latencies(configurations)
    print("Plotting throughput per dataset size...")
    plot_throughput_per_dataset_size(configurations)
    print("Plotting throughput per strategy...")
    plot_throughput_per_strategy(configurations)
    print("Done")
