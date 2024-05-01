import requests
import os
import shutil
import bz2
import xml.etree.ElementTree as ET
import psycopg2
import sys
from psycopg2.extras import execute_batch
from typing import Union
from elasticsearch import Elasticsearch


DUMP_HOST_URL = "https://dumps.wikimedia.org"
ARTICLES_DIR = "articles"


def get_all_files():
    dumpstatus_url = f"{DUMP_HOST_URL}/enwiki/20240401/dumpstatus.json"
    response = requests.get(dumpstatus_url).json()
    article_files = response['jobs']['articlesdump']['files']


    keys = list(article_files.keys())

    print(f"Downloading {len(keys)} files\n")

    for i, key in enumerate(keys):
        url = f"{DUMP_HOST_URL}{article_files[key]['url']}"
        print(f"Downloading {i+1}/{len(keys)}: {url}")
        print(f"Size: {article_files[key]['size'] * 1e-6:.2f} MB")

        file = os.path.join(ARTICLES_DIR, "compressed", key)
        with requests.get(url, stream=True) as r:
            with open(file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        print(f"Finished downloading: {file}")
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

    pages: list[Union[str, str]] = []
    for page in root.findall(tag("page")):
        title = page.find(tag('title')).text
        revision = page.find(tag('revision'))
        text = revision.find(tag('text'))
        pages.append((title, text.text))

    print(f"Loaded {len(pages)} pages")

    return pages


def insert_into_postgres(pages: list[Union[str, str]]):
    con = psycopg2.connect("postgresql://cosyp-sa:123@localhost:5049/cosyp")
    cur = con.cursor()

    print("Inserting pages into Postgres")
    execute_batch(
        cur, "INSERT INTO articles (title, body) VALUES (%s, %s)", pages)
    con.commit()
    print("Inserted pages into Postgres")

    # To create a full text search index:
    #
    #   ALTER TABLE articles ADD COLUMN search_vector tsvector;
    #   UPDATE articles SET search_vector = to_tsvector('english', title || ' ' || content);
    #   CREATE INDEX articles_search_vector_idx ON articles USING gin(search_vector);
    #
    # To search:
    #
    #   SELECT title, ts_rank(search_vector, to_tsquery('english', 'search term')) as rank
    #   FROM articles
    #   WHERE search_vector @@ to_tsquery('english', 'search term')
    #   ORDER BY rank DESC;


def insert_into_elasticsearch(pages: list[Union[str, str]]):
    es = Elasticsearch("http://localhost:9200")

    print("Indexing documents in Elasticsearch")

    for i, page in enumerate(pages, start=1):
        title, body = page
        doc = {"title": title, "body": body}
        es.index(index="articles", id=title, document=doc)

        if i % 100 == 0 or i == 1:
            print(f"\rIndexed {i} documents", end="")

    print("\rIndexed documents in Elasticsearch")

    # Query:
    #   es.search(index="articles", query={'match':{'body':'serach term'}}, fields=["title"], source=False)

def handle_data_loading():

    datadir_path = "articles/decompressed/"

    loaddata = None # Declare loaddata function
    mode = "--both" if len(sys.argv) < 3 else sys.argv[2]
    match mode:
        case "--postgres":
            loaddata = lambda pages: insert_into_postgres(pages)
        case "--elastic":
            loaddata = lambda pages: insert_into_elasticsearch(pages)
        case "--both":
            loaddata = lambda pages: insert_into_postgres(pages); insert_into_elasticsearch(pages)
        case _:
            print("Invalid load category")
            sys.exit(1)
    pass

    decompressed_dir = os.scandir(datadir_path)

    for io_entry in decompressed_dir:
        if io_entry.is_file():
            pages = load_articles_xml(io_entry.path)
            loaddata(pages)

def main():
    if len(sys.argv) < 2:
        print("Usage: python populate_data.py <command>")
        sys.exit(1)

    match sys.argv[1]:
        case "download":
            get_all_files()
        case "decompress":
            decompress_articles()
        case "load":
            handle_data_loading()
        case _:
            print("Invalid command")
            sys.exit(1)
    pass


if __name__ == '__main__':
    main()
