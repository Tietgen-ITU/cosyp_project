import psycopg2
import time
from elasticsearch import Elasticsearch
from generate_queries import generate_queries
import sys
import json


LIMIT = 5
IS_VERBOSE = "-v" in sys.argv


def connect():
    con = psycopg2.connect("postgresql://cosyp-sa:123@localhost:5049/cosyp")
    pg = con.cursor()
    es = Elasticsearch("http://localhost:9200")
    return pg, es


def measure_query(search_term, runners):
    bench = {
        "search_term": search_term,
        "elapsed_ms": {}
    }

    for name, runner in runners:
        start = time.monotonic_ns()
        runner(search_term)
        end = time.monotonic_ns()

        bench["elapsed_ms"][name] = (end - start) * 1e-6

    return bench


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

    query_settings = {
        "num_terms": 2500,
        "max_articles": 1000,
        "seed": 42,
    }

    print(f"Generating {query_settings['num_terms']} search terms...")
    start = time.monotonic()
    search_terms = generate_queries(pg, **query_settings)
    end = time.monotonic()
    print(f"Generated search terms in {end - start:.2f}s")

    for i, term in enumerate(search_terms):
        bench = measure_query(term, runners)
        bench["index"] = i
        print(json.dumps(bench, indent=2 if IS_VERBOSE else None), flush=True)
