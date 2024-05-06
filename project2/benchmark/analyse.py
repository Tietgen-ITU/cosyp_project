import json
import sys

def analyse_bench(file):
    with open(file, "r") as bench_file:
        bench = json.load(bench_file)

    print(f"Configuration: {bench['configuration']}")

    names = list(bench["runners"].keys())

    for name in names:
        all_latencies = [q["elapsed_ms"] for q in bench["runners"][name]["queries"]]
        avg_latency = sum(all_latencies) / len(all_latencies)

        print(f"{name}:")
        print(f"  Avg latency: {avg_latency:.2f} ms")
        print(f"  99th percentile: {sorted(all_latencies)[int(len(all_latencies) * 0.99)]:.2f} ms")
        print(f"  1st percentile: {sorted(all_latencies)[int(len(all_latencies) * 0.01)]:.2f} ms")
        print(f"  Throughput: {len(all_latencies) / (bench['runners'][name]['total_elapsed_ms'] / 1000):.2f} queries/second")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyse.py <bench_file>")
        sys.exit(1)

    analyse_bench(sys.argv[1])
