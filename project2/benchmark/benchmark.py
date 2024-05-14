import psycopg2
import time
from elasticsearch import Elasticsearch
from generate_queries import generate_search_terms
import os
import json
import hashlib
from datetime import datetime
import docker
from multiprocessing import Process, Queue


LIMIT = 5

STRATEGY_BATCH = "batch"
STRATEGY_SINGLE = "single"

POSTGRES_NAME = 'postgres'
ELASTICSEARCH_NAME = 'elasticsearch'


def connect():
    con = psycopg2.connect("postgresql://cosyp-sa:123@localhost:5049/cosyp")
    pg = con.cursor()
    es = Elasticsearch("http://localhost:9200", request_timeout=1000000)
    return pg, es


def measure_query(id, search_terms, runner):
    start = time.monotonic_ns()
    runner(search_terms)
    end = time.monotonic_ns()

    return {
        "id": id,
        "elapsed_ms": (end - start) * 1e-6
    }


def make_postgres_query(term):
    return f"""
        SELECT title, ts_rank(search_vector, query) as rank
        FROM articles, plainto_tsquery('english', '{term}') query
        WHERE query @@ search_vector
        ORDER BY rank DESC
        LIMIT {LIMIT};
    """


def query_postgres(cur, terms: list[str]):
    query = '\n'.join(make_postgres_query(term) for term in terms)

    cur.execute(query)
    results = cur.fetchall()

    return results


def query_elasticsearch(es, terms: list[str]):
    if len(terms) == 1:
        term = terms[0]
        res = es.search(index="articles", query={
                        'match': {'body': term}}, fields=["title"], source=False, size=LIMIT)
    else:
        searches = []
        for term in terms:
            searches.append({
                "index": "articles",
            })
            searches.append({
                "query": {
                    'match': {'body': term}
                },
                '_source': False,
                'size': LIMIT
            })
        res = es.msearch(index="articles", searches=searches)

    return res


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
        (POSTGRES_NAME, lambda terms: query_postgres(pg, terms)),
        (ELASTICSEARCH_NAME, lambda terms: query_elasticsearch(es, terms))
    ]

    n = configuration['num_queries']

    print(f"Generating {n} search terms...")
    start = time.monotonic()

    search_term_categories = generate_search_terms(
        pg,
        num_queries=n,
        num_words=configuration['num_words'],
        max_articles_sourced=configuration['max_articles_sourced'],
        seed=configuration['seed'])
    search_terms = search_term_categories[configuration['query_type']]

    end = time.monotonic()
    print(f"Generated search terms in {end - start:.2f}s")

    bench = {
        "configuration": configuration,
        "runners": {},
        "search_terms": search_terms,
    }

    for name, runner in runners:
        out = []

        p, queue = None, None
        if configuration['with_system_stats']:
            queue = Queue()
            p = Process(target=measure_container_stats, args=(name, queue))
            p.start()

        runner_start = time.monotonic_ns()

        if configuration['strategy'] == STRATEGY_SINGLE:
            for i, term in enumerate(bench["search_terms"]):
                if i % 10 == 0:
                    print(f"\rProgress for {name}: query {i}/{n}...", end="")

                query_bench = measure_query(i, [term], runner)
                out.append(query_bench)

            print(f"\rProgress for {name}: query {n}/{n}...")
        elif configuration['strategy'] == STRATEGY_BATCH:
            print(f"\rProgress for {name}: query 0/1...", end="")
            query_bench = measure_query(
                list(range(0, n+1)), bench["search_terms"], runner)
            out.append(query_bench)
            print(f"\rProgress for {name}: query 1/1...")

        runner_end = time.monotonic_ns()

        if configuration['with_system_stats']:
            p.terminate()

        usage_stats = []
        try:
            if configuration['with_system_stats']:
                usage_stats = drain_queue(queue)
        except Exception as e:
            print(f"Failed to get usage stats for {name}: {e}")

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

    num_words = [(1, 1), (2, 2), (4, 4), (8, 8), (16, 16),
                 (32, 32), (64, 64), (128, 128)]
    strategies = [STRATEGY_BATCH, STRATEGY_SINGLE]
    query_types = ["random", "no_matches", "in_few_articles", "in_many_articles"]
    repetitions = 1
    SEED = 42
    num_queries = [500]

    with_system_stats = True

    for repetition in range(repetitions):
        for nq in num_queries:
            for strategy in strategies:
                for nw in num_words:
                    for qt in query_types:
                        configurations.append({
                            "num_queries": nq,
                            "strategy": strategy,
                            "num_words": nw,
                            "max_articles_sourced": 50000,
                            "seed": SEED,
                            "repetition": repetition,
                            "with_system_stats": with_system_stats,
                            "query_type": qt
                        })

    for i, configuration in enumerate(configurations, start=1):
        start = time.monotonic()
        print(f"Running configuration {i}/{len(configurations)}: {configuration}")
        run_configuration(pg, es, BENCH_DIR, configuration)
        end = time.monotonic()
        print(f"Configuration {i}/{len(configurations)} completed in {end - start:.2f}s")
        print()
