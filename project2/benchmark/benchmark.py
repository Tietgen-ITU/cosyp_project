import psycopg2
import time
from elasticsearch import Elasticsearch
from generate_queries import generate_search_terms
import sys
import json


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


if __name__ == "__main__":
    pg, es = connect()

    runners = [
        ('postgres', lambda term: query_postgres(pg, term)),
        ('elasticsearch', lambda term: query_elasticsearch(es, term))
    ]

    workload_settings = {
        "num_queries": 5,
        "max_articles_sourced": 1000,
        "seed": 42,
    }

    n = workload_settings['num_queries']

    print(f"Generating {n} search terms...")
    start = time.monotonic()
    search_terms = generate_search_terms(pg, **workload_settings)
    end = time.monotonic()
    print(f"Generated search terms in {end - start:.2f}s")

    # TODO: Restructure so we can send many queries at once
    # Workload = collection of queries
    # Record time for each query and time in total
    # Can calc avg latency, throughput, 99% percentile.
    # Long-running allows us to measure memory usage, CPU usage, L3 cache misses, etc.
    # Maybe look into using perf to hook onto a running process.

    bench = {
        "workload": workload_settings,
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

    with open("bench.json", "w") as bench_file:
        bench_file.write(json.dumps(bench, indent=2))
