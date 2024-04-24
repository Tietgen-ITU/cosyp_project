import psycopg2
import string
import random
import time
from elasticsearch import Elasticsearch

con = psycopg2.connect("postgresql://cosyp-sa:123@localhost:5049/cosyp")
cur = con.cursor()
es = Elasticsearch("http://localhost:9200")


def generate_queries():
    random_query = """
        SELECT title, body FROM articles TABLESAMPLE SYSTEM(1)
    """
    cur.execute(random_query)

    all = cur.fetchall()

    special_chars = set()
    for _, body in all:
        special_chars.update(set(body))
    for letter in string.ascii_lowercase + string.ascii_uppercase:
        special_chars.discard(letter)

    banned = set(["REDIRECT", "ref", "nbsp"])

    queries = []
    for i, (_, body) in enumerate(all):
        trans = {c: " " for c in special_chars}
        table = str.maketrans(trans)
        normalised = body.translate(table)
        parts = [x for x in normalised.split() if len(x) >
                 1 and x not in banned]

        length = min(random.randint(1, 6), len(parts))
        start_index = random.randint(0, len(parts) - length)

        query = " ".join(parts[start_index:start_index + length])

        queries.append(query)

    return queries


if __name__ == "__main__":
    queries = generate_queries()

    LIMIT = 5

    for i, term in enumerate(queries[:5]):
        query = f"""
            SELECT title, ts_rank(search_vector, plainto_tsquery('english', %(term)s)) as rank
            FROM articles
            WHERE search_vector @@ plainto_tsquery('english', %(term)s)
            ORDER BY rank DESC
            LIMIT {LIMIT};
        """

        start = time.time()
        cur.execute(query, {"term": term})
        alles = cur.fetchall()
        end = time.time()

        print(f"{i}) Postgres results for '{term}' ({end - start:.2f}s)")
        for title, rank in alles:
            print("  ", f"{rank:05} | {title}")

        start = time.time()
        res = es.search(index="articles", query={
                        'match': {'body': term}}, fields=["title"], source=False, size=LIMIT)
        end = time.time()

        print()

        print(f"{i}) Elasticsearch results for '{term}' ({end - start:.2f}s)")
        for hit in res['hits']['hits']:
            print("  ", f'{hit["_score"]:05}', "|", hit['fields']['title'][0])

        print()
        print()
