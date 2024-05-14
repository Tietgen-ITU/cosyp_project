import requests
import os
import shutil
import json
import bz2
import xml.etree.ElementTree as ET
import psycopg2
import sys
from wikitextparser import parse
from psycopg2.extras import execute_batch
from typing import Union
from elasticsearch import Elasticsearch, helpers
import time


DUMP_HOST_URL = "https://dumps.wikimedia.org"
ARTICLES_DIR = "articles"
PLAINTEXT_DIR = os.path.join(ARTICLES_DIR, "plaintext")


def get_all_files():
    dumpstatus_url = f"{DUMP_HOST_URL}/enwiki/20240401/dumpstatus.json"
    response = requests.get(dumpstatus_url).json()
    article_files = response['jobs']['articlesdump']['files']


    keys = list(article_files.keys())

    print(f"Downloading {len(keys)} files\n")

    for i, key in enumerate(keys):
        start = time.time()

        url = f"{DUMP_HOST_URL}{article_files[key]['url']}"
        print(f"Downloading {i+1}/{len(keys)}: {url}")
        print(f"Size: {article_files[key]['size'] * 1e-6:.2f} MB")

        file = os.path.join(ARTICLES_DIR, "compressed", key)
        with requests.get(url, stream=True) as r:
            with open(file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        end = time.time()
        print(f"Finished downloading: {file}")
        print(f"Took {end - start:.1f} seconds")
        print()


def decompress_articles():
    archive_dir = os.path.join(ARTICLES_DIR, "compressed")
    decompressed_dir = os.path.join(ARTICLES_DIR, "decompressed")

    for file in os.listdir(archive_dir):
        archive_path = os.path.join(archive_dir, file)
        decompressed_path = os.path.join(
            decompressed_dir, file.replace(".bz2", ""))

        print(f"Decompressing {archive_path}")
        with open(archive_path, 'rb') as source, open(decompressed_path, 'wb') as dest:
            dest.write(bz2.decompress(source.read()))

        print(f"Decompressed {file} to {decompressed_path}")
        print()


def load_articles_xml(file):
    print(f"Parsing {file}")
    tree = ET.parse(file)
    print(f"Parsed {file}")

    print("Reading pages")
    root = tree.getroot()

    def tag(x): return f"{{http://www.mediawiki.org/xml/export-0.10/}}{x}"
    def untag(x): return x.replace(
        "{http://www.mediawiki.org/xml/export-0.10/}", "")
    pages: list[dict[str, str]] = []

    for page in root.findall(tag("page")):
        title = page.find(tag('title')).text
        revision = page.find(tag('revision'))
        text = revision.find(tag('text')).text
        if text is None:
            continue

        parsed_text = parse(text).plain_text()
        parsed_text = parsed_text.replace("#REDIRECT", "#REDIRECT ")

        pages.append({"title": title, "body": parsed_text})

    print(f"Loaded {len(pages)} pages")

    return pages


def insert_into_postgres(pages: list[dict[str, str]], port: str):
    con = psycopg2.connect("postgresql://cosyp-sa:123@localhost:" + port + "/cosyp")
    cur = con.cursor()

    print("Inserting pages into Postgres")
    execute_batch(
        cur, "INSERT INTO articles (title, body) VALUES (%(title)s, %(body)s)", pages)
    con.commit()
    print("Inserted pages into Postgres")

    # To create a full text search index:
    #
    #   ALTER TABLE articles ADD COLUMN search_vector tsvector;
    #   UPDATE articles SET search_vector = to_tsvector('english', body);
    #   CREATE INDEX articles_search_vector_idx ON articles USING gin(search_vector);
    #
    # To search:
    #
    #   SELECT title, ts_rank(search_vector, to_tsquery('english', 'search term')) as rank
    #   FROM articles
    #   WHERE search_vector @@ to_tsquery('english', 'search term')
    #   ORDER BY rank DESC;


def insert_into_elasticsearch(pages: list[dict[str, str]], port: str):
    es = Elasticsearch("http://localhost:"+port)

    print("Indexing documents in Elasticsearch")
    helpers.bulk(es, pages, index="articles")
    print("\rIndexed documents in Elasticsearch")

    # Query:
    #   es.search(index="articles", query={'match':{'body':'serach term'}}, fields=["title"], source=False)

def get_port():

    if len(sys.argv) < 5:
        print("Usage: python populate_data.py load <mode> -p <port> -s <size in gb>")
        sys.exit(1)

    return sys.argv[4]

def get_target_size_gb():

        if len(sys.argv) < 7:
            print("Usage: python populate_data.py load <mode> -p <port> -s <size in gb>")
            sys.exit(1)

        return int(sys.argv[6])

def handle_data_loading():
    loaddata = None # Declare loaddata function
    mode = "--both" if len(sys.argv) < 3 else sys.argv[2]
    match mode:
        case "--postgres":
            loaddata = lambda pages, port: insert_into_postgres(pages, port)
        case "--elastic":
            loaddata = lambda pages, port: insert_into_elasticsearch(pages, port)
        case "--both":
            loaddata = lambda pages, port: (insert_into_postgres(pages, port), insert_into_elasticsearch(pages, port))
        case _:
            print("Invalid load category")
            sys.exit(1)
    pass

    port = get_port()
    size_gb = get_target_size_gb()
    gb_multiplier = 1000000000
    target_size = size_gb*gb_multiplier

    dir_contents = os.scandir(PLAINTEXT_DIR)

    files = [file for file in dir_contents if file.is_file()]
    files.sort(key=lambda x: x.stat().st_size, reverse=True)

    for io_entry in files:
        if target_size < io_entry.stat().st_size:
            continue

        target_size -= io_entry.stat().st_size

        print(f"Loading {io_entry.stat().st_size / gb_multiplier:.1f} GB from {io_entry.name}")
        start = time.monotonic()
        with open(io_entry) as f:
            pages = json.load(f)
        end = time.monotonic()
        print(f"Finished loading in {end - start:.1f}s")

        loaddata(pages, port)


def handle_plaintext():
    datadir_path = "articles/decompressed/"
    decompressed_dir = os.scandir(datadir_path)

    files = [file for file in decompressed_dir if file.is_file()]
    num = int(sys.argv[2])

    count = 0
    iter_count = 11
    number_of_skip_files = num*iter_count

    out_dir = PLAINTEXT_DIR

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    for io_entry in files:
        if number_of_skip_files > 0:
            number_of_skip_files -= 1
            continue

        if count >= iter_count:
            continue

        count += 1
        pages = load_articles_xml(io_entry.path)

        out_file = os.path.join(out_dir, io_entry.name + ".json")
        print(f"Writing {len(pages)} pages to {out_file}")
        with open(out_file, "w") as f:
            json.dump(pages, f)
        print(f"Wrote to {out_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python populate_data.py <command>")
        sys.exit(1)

    match sys.argv[1]:
        case "download":
            get_all_files()
        case "decompress":
            decompress_articles()
        case "plaintext":
            handle_plaintext()
        case "load":
            handle_data_loading()
        case _:
            print("Invalid command")
            sys.exit(1)
    pass


if __name__ == '__main__':
    main()
