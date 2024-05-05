import string
import random


def generate_queries(cur):
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
