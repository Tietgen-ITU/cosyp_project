from matplotlib.axes import mticker
import matplotlib.pyplot as plt
from dataclasses import dataclass
import os
import sys
import json


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


MARKERS = [('*', None), ('s', None), ('|', None),
           ('x', None), ('s', 'none'), ('o', 'none')]


def read_data(folder):
    configs = []

    for filename in os.listdir(folder):
        file = os.path.join(folder, filename)
        config = Configuration.from_file(file)
        configs.append(config)

    print(f"Loaded {len(configs)} experiments")

    return configs


def plot_throughput(configurations: list[Configuration]):

    strategies = ["batch", "single"]
    runners = ["postgres", "elasticsearch"]

    configurations.sort(key=lambda x: x.config()["num_words"])

    for strategy in strategies:
        plt.figure(figsize=(13, 5))

        for i, runner in enumerate(runners):
            confs = [c for c in configurations if c.config()["strategy"] == strategy]

            xs = [c.config()["num_words"][0] for c in confs]
            ys = [c.metrics(runner).throughput for c in confs]
            marker, facecolor = MARKERS[i]

            plt.plot(xs, ys, f'-{marker}', markerfacecolor=facecolor, label=runner)

        ax = plt.gca()
        ax.set_xscale('log', base=2)
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

        plt.xlabel("Number of words in search term")
        plt.ylabel("Throughput (queries/second)")
        plt.grid()
        plt.title(f"Throughput for different query sizes ({strategy})")
        plt.legend()

        save_plot(f"throughput-{strategy}")


def plot_variance(configurations: list[Configuration]):

    runners = ["postgres", "elasticsearch"]
    strategies = ["single", "batch"]

    configurations.sort(key=lambda x: x.config()["num_words"])

    for strategy in strategies:
        plt.figure(figsize=(13, 5))

        for i, runner in enumerate(runners):
            plt.subplot(1, len(runners), i + 1)

            confs = [c for c in configurations if c.config()["strategy"] == strategy]

            xs = [c.config()["num_words"][0] for c in confs]
            ys = [c.latencies(runner) for c in confs]

            plt.boxplot(ys, labels=xs, showmeans=True)

            plt.title(f"Latencies for {runner} ({strategy})")
            plt.xlabel("Number of words in search term")
            plt.ylabel("Latency (ms)")
            plt.grid()

        save_plot(f"variance-{strategy}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <dir path>")
        exit(1)

    configurations = read_data(sys.argv[1])

    for c in configurations:
        print(c.config())

    plot_throughput(configurations)
    plot_variance(configurations)
