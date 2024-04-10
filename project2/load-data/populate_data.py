import requests
import os
import shutil
import bz2


DUMP_HOST_URL = "https://dumps.wikimedia.org"
ARTICLES_DIR = "articles"


def get_all_files():
    dumpstatus_url = f"{DUMP_HOST_URL}/enwiki/20240401/dumpstatus.json"
    response = requests.get(dumpstatus_url).json()
    article_files = response['jobs']['articlesdump']['files']

    keys = [list(article_files.keys())[0]]

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
        decompressed_path = os.path.join(decompressed_dir, file.replace(".bz2", ""))

        print(f"Decompressing {archive_path}")
        with open(archive_path, 'rb') as source, open(decompressed_path, 'wb') as dest:
            dest.write(bz2.decompress(source.read()))

        print(f"Decompressed {file} to {decompressed_path}")
        print()

def main():
    # get_all_files()
    # decompress_articles()
    pass

if __name__ == '__main__':
    main()
