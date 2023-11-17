import os
import re
import argparse
import requests
from bs4 import BeautifulSoup
from transmission_rpc import Client


TRANSMISSION = {
    "host": os.environ.get("TRANS_HOST", "localhost"),
    "port": int(os.environ.get("TRANS_PORT", 9091)),
    "user": os.environ.get("TRANS_USER", "transmission"),
    "pass": os.environ.get("TRANS_PASS", "password"),
}


class TorrentProvider:
    def search(self, query):
        raise NotImplementedError


class SolidTorrent(TorrentProvider):
    API = "https://solidtorrents.to/search?sort=date&q={}"

    def search(self, query):
        return self._do_query(query)

    def _do_query(self, query):
        resp = requests.get(self.API.format(query))
        if not resp.ok:
            return

        for title, link in self._parse(resp.content):
            yield title, link

    def _parse(self, html):
        root = BeautifulSoup(html, "html.parser")
        for card in root.find_all("li", "search-result"):
            title = card.find("h5", "title")
            title = ''.join(title.stripped_strings)
            magnet = card.find_all("a", "dl-magnet")[0].attrs["href"]
            yield title, magnet


Providers = [SolidTorrent()]


def add_to_transmission(link):
    c = Client(host=TRANSMISSION["host"],
               port=TRANSMISSION["port"],
               username=TRANSMISSION["user"],
               password=TRANSMISSION["pass"])
    if link.startswith("magnet"):
        c.add_torrent(link)
    else:
        r = requests.get(torrent_url)
        c.add_torrent(r.content)


def run():
    parser = argparse.ArgumentParser(prog="autotr",
                                     description="Look for torrent")
    parser.add_argument("-d", action="store_true",
                        help="Add the torrent to transmission")
    parser.add_argument("-a", action="store_true",
                        help="Show all the found torrents")
    parser.add_argument("query", nargs=1)
    args = parser.parse_args()

    for provider in Providers:
        for title, link in provider.search(args.query[0]):
            print(f"- {title}")
            if args.d:
                add_to_transmission(link)
            if not args.a:
                break
