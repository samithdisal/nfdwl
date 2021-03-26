import os
import sys
import time
from typing import Optional

import click
import requests
from bs4 import BeautifulSoup
from mkepub import mkepub

BASE_URL = "https://novelfull.com"


__normalize_map = {
    ord("–"): "-",
    ord("“"): "\"",
    ord("”"): "\"",
    ord("’"): "'",
}


def normalise_str(inp: bytes) -> str:
    return str(inp.decode("utf-8").translate(__normalize_map).encode("ascii", "ignore"), encoding="ascii")


def get_chapter_urls(url: str):
    content = requests.get(url)
    assert content.status_code == 200
    soup = BeautifulSoup(normalise_str(content.content))
    assert soup, "Cannot parse chapter urls"
    return [(option.text, option.attrs['value']) for option in soup.find_all("option")]


def get_chapter(url: str):
    full_url = f"{BASE_URL}{url}"
    content = requests.get(full_url)
    assert content.status_code == 200
    return normalise_str(content.content)


def add_chapter(title: str, content: str, book: mkepub.Book):
    soup = BeautifulSoup(content)
    chapter = soup.find("div", {"id": "chapter-content"})
    for i in chapter.find_all("a"):
        i.decompose()
    for i in chapter.find_all("script"):
        i.decompose()
    last_div = chapter.find_all("div")[-1]
    last_div.decompose()
    book.add_page(title, chapter)
    print(f"Adding chapter {title}")
    time.sleep(6)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield i, i+n, lst[i:i + n]


@click.command()
@click.argument("title")
@click.argument("url")
def main(title: str, url: str, chunk_size: int = 100, start_idx: int = 0, end_idx: int = 0) -> int:
    chapter_urls = get_chapter_urls(url)
    if start_idx and end_idx:
        if start_idx < 0 or end_idx < 0:
            print("start index and end index should be positive values")
            return 1
        if start_idx < end_idx:
            if start_idx > len(chapter_urls)-1 or end_idx > len(chapter_urls):
                print("indexes are larger than chapter list length")
                return 1
            chapter_urls = chapter_urls[start_idx:end_idx]
        else:
            print("start index cannot be larger than end index")
            return 1
    elif start_idx:
        if start_idx > 0:
            if start_idx > len(chapter_urls)-1:
                print("indexes are larger than chapter list length")
                return 1
            chapter_urls = chapter_urls[start_idx:]
        else:
            print("start index should be positive")
            return 1

    c_urls = chunks(chapter_urls, 100)

    for c in c_urls:
        book = mkepub.Book(title=f"{title} Chapter {int(c[0])+1} to {int(c[1])}")
        for chapter_title, chapter_url in c[2]:
            add_chapter(f"{chapter_title}", get_chapter(chapter_url), book)
            time.sleep(1)
        filename = f"{title.replace(' ', '_')}_{int(c[0])+1}_{c[1]}.epub"
        if os.path.exists(filename):
            os.remove(filename)
        book.save(filename)
        print(f"Saving book {filename}")
        time.sleep(60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
