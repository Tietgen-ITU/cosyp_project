import psycopg2
import time
from elasticsearch import Elasticsearch
from generate_queries import generate_search_terms
import sys
import os
import json
import hashlib
from datetime import datetime


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


def run_configuration(pg, es, out_dir, configuration):
    runners = [
        ('postgres', lambda term: query_postgres(pg, term)),
        ('elasticsearch', lambda term: query_elasticsearch(es, term))
    ]

    n = configuration['num_queries']

    print(f"Generating {n} search terms...")
    start = time.monotonic()

    search_terms = generate_search_terms(
        pg,
        num_queries=n,
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

        bench["runners"][name] = {
            "total_elapsed_ms": (runner_end - runner_start) * 1e-6,
            "queries": out
        }

        print(f"\rProgress for {name}: query {n}/{n}...")

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

    configurations = [
        {
            "num_queries": 500,
            "max_articles_sourced": 1000,
            "seed": 42,
            "repetition": 1
        }
    ]

    for configuration in configurations:
        run_configuration(pg, es, BENCH_DIR, configuration)
