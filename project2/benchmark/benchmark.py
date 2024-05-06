import psycopg2
import time
from elasticsearch import Elasticsearch
from generate_queries import generate_search_terms
import sys
import os
import json
import hashlib
from datetime import datetime
import docker
from multiprocessing import Process, Queue


LIMIT = 5
IS_VERBOSE = "-v" in sys.argv


def connect():
    con = psycopg2.connect("postgresql://cosyp-sa:123@localhost:5049/cosyp")
    pg = con.cursor()
    es = Elasticsearch("http://localhost:9200")
    return pg, es


def measure_query(id, search_term, runner):
    start = time.monotonic_ns()
    runner(search_term)
    end = time.monotonic_ns()

    return {
        "id": id,
        "elapsed_ms": (end - start) * 1e-6
    }


def query_postgres(cur, term):
    query = f"""
        SELECT title, ts_rank(search_vector, plainto_tsquery('english', %(term)s)) as rank
        FROM articles
        WHERE search_vector @@ plainto_tsquery('english', %(term)s)
        ORDER BY rank DESC
        LIMIT {LIMIT};
    """

    cur.execute(query, {"term": term})
    results = cur.fetchall()

    # print(f"{i}) Postgres results for '{term}'")
    # for title, rank in results:
    #     print("  ", f"{rank:05} | {title}")

    return results


def query_elasticsearch(es, term):
    res = es.search(index="articles", query={
                    'match': {'body': term}}, fields=["title"], source=False, size=LIMIT)

    # print(f"{i}) Elasticsearch results for '{term}'")
    # for hit in res['hits']['hits']:
    #     print("  ", f'{hit["_score"]:05}', "|", hit['fields']['title'][0])

    return res


POSTGRES_NAME = 'postgres'
ELASTICSEARCH_NAME = 'elasticsearch'


def measure_container_stats(name, queue):
    docker_client = docker.from_env()

    containers = {}
    containers[POSTGRES_NAME] = "cosyp-postgres"
    containers[ELASTICSEARCH_NAME] = "cosyp-elastic"

    container = docker_client.containers.get(containers[name])

    for stats in container.stats(decode=True):
        try:
            mem_bytes_used = stats["memory_stats"]["usage"]
            mem_bytes_avail = stats["memory_stats"]["limit"]
            mem_gb_used = round(mem_bytes_used / (1024*1024*1024), 1) 
            mem_gb_avail = round(mem_bytes_avail / (1024*1024*1024), 1) 

            cpu_usage = (stats['cpu_stats']['cpu_usage']['total_usage']
                         - stats['precpu_stats']['cpu_usage']['total_usage'])
            cpu_system = (stats['cpu_stats']['system_cpu_usage']                    
                          - stats['precpu_stats']['system_cpu_usage'])
            num_cpus = stats['cpu_stats']["online_cpus"]
            cpu_perc = round((cpu_usage / cpu_system) * num_cpus * 100)
            cpu_max_perc = num_cpus * 100

            queue.put({
                "mem_gb_used": mem_gb_used,
                "mem_gb_avail": mem_gb_avail,
                "cpu_perc": cpu_perc,
                "cpu_max_perc": cpu_max_perc
            })
        except Exception as e:
            pass


def drain_queue(q):
    q.put(None)
    return list(iter(lambda: q.get(timeout=0.00001), None))


def run_configuration(pg, es, out_dir, configuration):
    runners = [
        (POSTGRES_NAME, lambda term: query_postgres(pg, term)),
        (ELASTICSEARCH_NAME, lambda term: query_elasticsearch(es, term))
    ]

    n = configuration['num_queries']

    print(f"Generating {n} search terms...")
    start = time.monotonic()

    search_terms = generate_search_terms(
        pg,
        num_queries=n,
        num_words=configuration['num_words'],
        max_articles_sourced=configuration['max_articles_sourced'],
        seed=configuration['seed'])

    end = time.monotonic()
    print(f"Generated search terms in {end - start:.2f}s")

    # TODO: Restructure so we can send many queries at once
    # Can calc avg latency, throughput, 99% percentile.
    # Long-running allows us to measure memory usage, CPU usage, L3 cache misses, etc.
    # Maybe look into using perf to hook onto a running process.

    bench = {
        "configuration": configuration,
        "runners": {},
        "search_terms": search_terms,
        "errors": []
    }

    for name, runner in runners:
        out = []

        queue = Queue()
        p = Process(target=measure_container_stats, args=(name, queue))
        p.start()

        runner_start = time.monotonic_ns()
        for i, term in enumerate(bench["search_terms"]):
            if i % 10 == 0:
                print(f"\rProgress for {name}: query {i}/{n}...", end="")

            try:
                query_bench = measure_query(i, term, runner)
                out.append(query_bench)
            except Exception as e:
                print(f"\nError running query {i}: {e}")
                bench["errors"].append({
                    "runner": name,
                    "query_index": i,
                    "error": str(e)
                })
        runner_end = time.monotonic_ns()

        print(f"\rProgress for {name}: query {n}/{n}...")

        p.terminate()

        usage_stats = drain_queue(queue)

        bench["runners"][name] = {
            "total_elapsed_ms": (runner_end - runner_start) * 1e-6,
            "queries": out,
            "stats": usage_stats
        }

    configuration_hash = hashlib.md5(json.dumps(
        configuration).encode()).hexdigest()
    filename = f"{out_dir}/bench-{configuration_hash}.json"

    print(f"Writing benchmark to {filename}")

    with open(filename, "w") as bench_file:
        bench_file.write(json.dumps(bench, indent=2))


if __name__ == "__main__":
    pg, es = connect()

    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    BENCH_DIR = f"benches/{folder_name}"
    if not os.path.exists(BENCH_DIR):
        os.makedirs(BENCH_DIR)


    configurations = []

    for interval in [(6, 6), (1,1), (25, 25)]:
        configurations.append({
            "num_queries": 500,
            "num_words": interval,
            "max_articles_sourced": 1000,
            "seed": 42,
            "repetition": 1
        })

    for configuration in configurations:
        print(f"Running configuration: {configuration}")
        run_configuration(pg, es, BENCH_DIR, configuration)
