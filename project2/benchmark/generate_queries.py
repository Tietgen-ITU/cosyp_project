from collections import defaultdict
import string
import random
from itertools import cycle
import json
import sys
import psycopg2
import os


STOP_WORDS = set("a, an, and, are, as, at, be, but, by, for, if, in, into, is, it, no, not, of, on, or, such, that, the, their, then, there, these, they, this, to, was, will, with".split(", "))


def load_word_freqs(path):
    # print("Loading word frequencies from", path)
    with open(path, "r") as f:
        word_freqs = json.load(f)
    # print("Loaded word frequencies")

    # print("Filtering words")
    banned = set(STOP_WORDS)
    for bw in banned:
        word_freqs.pop(bw, None)
    # print("Filtered words")

    # items = list(word_freqs.items())
    # print(f"Total number of words {len(items):,}")
    # print(f"Total number of occurrences: {sum(item[1] for item in items):,}")
    # percentiles = [0.0001, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9]
    # for p in percentiles:
    #     index = int(len(items) * p)
    #     print(f"{p * 100}-percentile:",
    #           items[index], f"({index:,} words appear at least {items[index][1]:,} times)")

    return word_freqs


word_article_freqs = None
cache_file = "search_terms_cache.json"


def make_article_freqs_filename(dataset_size_gb=None):
    suffix = "" if dataset_size_gb is None else f"_{dataset_size_gb}gb"
    return f"word_article_freqs{suffix}.json"


def generate_search_terms(cur, num_queries=10, max_articles_sourced=1000, num_words=(1, 6), seed=None, dataset_size_gb=None):
    if not os.path.exists(cache_file):
        with open(cache_file, "w") as f:
            json.dump({}, f)
    with open(cache_file, "r") as f:
        current_cache = json.load(f)
    cache_key = f"{num_queries}_{max_articles_sourced}_{num_words[0]}-{num_words[1]}_{seed}_{dataset_size_gb}gb"

    if cache_key in current_cache:
        print("Using cached search terms for key", cache_key)
        return current_cache[cache_key]

    global word_article_freqs
    if word_article_freqs is None:
        freq_file = make_article_freqs_filename(dataset_size_gb)
        print("Loading word article frequencies from", freq_file)
        word_article_freqs = load_word_freqs(freq_file)

    random.seed(seed)

    print("Fetching articles")
    random_query = f"""
        SELECT title, body FROM articles
        TABLESAMPLE SYSTEM(100)
        {f"REPEATABLE({seed})" if seed else ""}
        WHERE LENGTH(body) > 100
        LIMIT {max_articles_sourced};
    """
    cur.execute(random_query)

    all = cur.fetchall()
    print(f"Done fetching {len(all)} articles")

    # If we want more search terms than articles fetched, wrap around
    articles_iter = cycle(all)

    special_chars = set()
    for _, body in all:
        special_chars.update(set(body))
    for letter in string.ascii_lowercase + string.ascii_uppercase:
        special_chars.discard(letter)

    banned = set(["REDIRECT", "ref", "nbsp", "s"])

    search_term_score = {}

    trans = {c: " " for c in special_chars}
    trans["'"] = ""
    table = str.maketrans(trans)

    min_words, max_words = num_words

    while len(search_term_score) < 100 * num_queries:
        print(
            f"\rProgress: {len(search_term_score)}/{100 * num_queries}", end="")
        _, body = next(articles_iter)

        normalised = body.translate(table)
        parts = [x for x in normalised.split() if x not in banned]

        length = random.randint(min_words, max_words)
        start_index = random.randint(0, len(parts))

        if start_index + length > len(parts):
            continue

        search_term = " ".join(parts[start_index:start_index + length])

        lower_terms = set(
            term for term in search_term.lower().split() if term not in STOP_WORDS)
        # with_score = [(term, word_freqs.get(term, 0)) for term in lower_terms]
        with_article_score = [(term, word_article_freqs.get(term, 0))
                              for term in lower_terms]

        # freq_score = sum(score for _, score in with_score)
        article_score = sum(score for _, score in with_article_score)

        # print(f"Search term: {search_term}")
        # print(f"Frequency score: {freq_score}")
        # print(f"Word frequency scores: {with_score}")
        # print(f"Article frequency score: {article_score}")
        # print(f"Word article scores: {with_article_score}")

        search_term_score[search_term.lower()] = (search_term, article_score)

    no_matches = []
    for _ in range(num_queries):
        parts = []
        for _ in range(max(num_words)):
            random_string = ''.join(
                random.choices(string.ascii_lowercase, k=16))
            parts.append(random_string)
        garbage_terms = random.sample(parts, random.randint(*num_words))
        no_matches.append(' '.join(garbage_terms))

    print(f"\nDone generating search terms")

    sorted_search_terms = sorted(
        search_term_score.values(), key=lambda x: x[1], reverse=True)

    # for search_term, score in sorted_search_terms:
    #     print(f"{score}: {search_term}")
    # print()

    high_cardinality = [term for term, _ in sorted_search_terms[:num_queries]]
    low_cardinality = [term for term, _ in sorted_search_terms[-num_queries:]]
    random_queries = [term for term, _ in random.sample(
        sorted_search_terms, num_queries)]

    results = {
        'in_many_articles': high_cardinality,
        'in_few_articles': low_cardinality,
        'random': random_queries,
        'no_matches': no_matches,
    }

    current_cache[cache_key] = results
    with open(cache_file, "w") as f:
        json.dump(current_cache, f, indent=2)

    return results


def count_words(cur, seed=None, dataset_size_gb=None):
    random.seed(seed)

    print("Fetching articles")
    random_query = f"""
        SELECT title, body FROM articles
        TABLESAMPLE SYSTEM(100)
        {f"REPEATABLE({seed})" if seed else ""};
    """
    cur.execute(random_query)

    all = cur.fetchall()
    print("Done fetching articles")

    special_chars = set()
    for _, body in all:
        special_chars.update(set(body))
    for letter in string.ascii_lowercase + string.ascii_uppercase:
        special_chars.discard(letter)

    trans = {c: " " for c in special_chars}
    trans["'"] = ""
    table = str.maketrans(trans)

    # word_freqs = defaultdict(lambda: 0)
    word_article_freqs = defaultdict(lambda: 0)

    for i, (_, body) in enumerate(all):
        if i % 100 == 0:
            print(f"\rProcessing article {i}/{len(all)}", end="")

        normalised = body.translate(table).lower()
        parts = [x for x in normalised.split()]

        # for part in parts:
        #     word_freqs[part.lower()] += 1

        for word in set(parts):
            word_article_freqs[word] += 1

    print()
    print("Done processing articles")

    # sorted_freqs = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)
    sorted_article_freqs = sorted(
        word_article_freqs.items(), key=lambda x: x[1], reverse=True)

    print("Writing to file")

    # with open("word_freqs.json", "w") as f:
    #     json.dump(dict(sorted_freqs), f, indent=2)
    with open(make_article_freqs_filename(dataset_size_gb), "w") as f:
        json.dump(dict(sorted_article_freqs), f, indent=2)

    print("Done writing to file")


def connect():
    postgres_con_string = os.environ.get('COSYP_PSQL_CONNECTION_STRING')
    if postgres_con_string is None:
        postgres_con_string = "postgresql://cosyp-sa:123@localhost:5049/cosyp"

    print(f"Connecting to Postgres via {postgres_con_string}")

    con = psycopg2.connect(postgres_con_string)
    pg = con.cursor()
    return pg


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("what should i do?")
        exit(1)

    dataset_size_gb = 2

    pg = connect()
    if sys.argv[1] == "count":
        print(count_words(pg, seed=42, dataset_size_gb=dataset_size_gb))
    elif sys.argv[1] == "gen":
        print(json.dumps(generate_search_terms(
            pg, seed=1337, num_words=(4, 4), dataset_size_gb=dataset_size_gb), indent=2))
    else:
        print("idk bro")
    pg.close()
