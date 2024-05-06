import string
import random
from itertools import cycle


def generate_search_terms(cur, num_queries=10, max_articles_sourced=1000, num_words=(1, 6), seed=None):
    random.seed(seed)

    random_query = f"""
        SELECT title, body FROM articles
        TABLESAMPLE SYSTEM(100)
        {f"REPEATABLE({seed})" if seed else ""}
        LIMIT {min(num_queries, max_articles_sourced)};
    """
    cur.execute(random_query)

    all = cur.fetchall()

    # If we want more search terms than articles fetched, wrap around
    articles_iter = cycle(all)

    special_chars = set()
    for _, body in all:
        special_chars.update(set(body))
    for letter in string.ascii_lowercase + string.ascii_uppercase:
        special_chars.discard(letter)

    banned = set(["REDIRECT", "ref", "nbsp"])

    search_terms = set()

    min_words, max_words = num_words

    while len(search_terms) < num_queries:
        _, body = next(articles_iter)

        trans = {c: " " for c in special_chars}
        table = str.maketrans(trans)
        normalised = body.translate(table)
        parts = [x for x in normalised.split() if len(x) >
                 1 and x not in banned]

        length = random.randint(min_words, max_words)
        start_index = random.randint(0, len(parts))

        if start_index + length > len(parts):
            continue

        search_term = " ".join(parts[start_index:start_index + length])

        search_terms.add(search_term)

    return list(search_terms)
