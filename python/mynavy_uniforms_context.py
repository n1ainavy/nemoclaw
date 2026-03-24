#!/usr/bin/env python3
"""Crawl the MyNavy HR Uniform Regulations site and export AI-ready context.

The crawler starts from the Uniform Regulations table of contents and walks the
chapter/article links that live under the Uniform Regulations path. It extracts
breadcrumb/title metadata plus the main body text from each page and writes the
result as JSONL for downstream indexing.

Example:
    python mynavy_uniforms_context.py \
        --output navy_uniforms_context.jsonl \
        --include-external-tables
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup, Tag

DEFAULT_START_URL = (
    "https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/"
    "Uniform-Regulations/Table-of-Contents/"
)
DEFAULT_ALLOWED_PREFIX = (
    "https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/"
)
DEFAULT_EXTERNAL_TABLE_HOSTS = {
    "mynavyhr.navy.afpims.mil",
}
USER_AGENT = "Mozilla/5.0 (compatible; NavyUniformsContextBot/1.0)"
TIMEOUT_SECONDS = 30
FOOTER_MARKERS = (
    "Need Career, Pay or Personnel help?",
    "NAVY PERSONNEL COMMAND",
    "This is an Official U.S. Navy Website",
)
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class CrawlTarget:
    url: str
    kind: str


class UniformRegulationsCrawler:
    def __init__(
        self,
        start_url: str,
        allowed_prefix: str,
        include_external_tables: bool = False,
        pause_seconds: float = 0.3,
        session: requests.Session | None = None,
    ) -> None:
        self.start_url = start_url
        self.allowed_prefix = allowed_prefix.rstrip("/") + "/"
        self.include_external_tables = include_external_tables
        self.pause_seconds = pause_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def crawl(self) -> list[dict]:
        queue = deque([CrawlTarget(self.start_url, "toc")])
        queued = {self._normalize_url(self.start_url)}
        visited = set()
        documents: list[dict] = []

        while queue:
            target = queue.popleft()
            url = self._normalize_url(target.url)
            if url in visited:
                continue

            response = self.session.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            visited.add(url)

            document = self._extract_document(url, soup, target.kind)
            documents.append(document)

            for link in self._discover_links(url, soup):
                normalized = self._normalize_url(link.url)
                if normalized in queued or normalized in visited:
                    continue
                queued.add(normalized)
                queue.append(CrawlTarget(normalized, link.kind))

            if self.pause_seconds:
                time.sleep(self.pause_seconds)

        return documents

    def _extract_document(self, url: str, soup: BeautifulSoup, kind: str) -> dict:
        main = soup.find("main") or soup.find(id="main-content") or soup.body
        breadcrumbs = [self._clean_text(a.get_text(" ", strip=True)) for a in soup.select("nav a, .breadcrumb a")]

        title = self._extract_title(main, soup)
        body_text = self._extract_main_text(main)
        headings = [
            self._clean_text(node.get_text(" ", strip=True))
            for node in main.select("h1, h2, h3, h4")
            if self._clean_text(node.get_text(" ", strip=True))
        ]

        return {
            "url": url,
            "kind": kind,
            "title": title,
            "breadcrumbs": breadcrumbs,
            "headings": headings,
            "content": body_text,
        }

    def _extract_title(self, main: Tag, soup: BeautifulSoup) -> str:
        for selector in ("h1", "h2", "title"):
            node = main.select_one(selector) if selector != "title" else soup.select_one("title")
            if node:
                value = self._clean_text(node.get_text(" ", strip=True))
                if value:
                    return value
        return "Untitled"

    def _extract_main_text(self, main: Tag) -> str:
        clone = BeautifulSoup(str(main), "html.parser")

        for node in clone.select("script, style, noscript, form, iframe, svg"):
            node.decompose()

        text_lines: list[str] = []
        for raw_line in clone.get_text("\n").splitlines():
            line = self._clean_text(raw_line)
            if not line:
                continue
            if line == "Start of main content":
                continue
            if any(marker in line for marker in FOOTER_MARKERS):
                break
            text_lines.append(line)

        return "\n".join(self._dedupe_adjacent(text_lines))

    def _discover_links(self, base_url: str, soup: BeautifulSoup) -> Iterable[CrawlTarget]:
        main = soup.find("main") or soup.find(id="main-content") or soup.body
        for anchor in main.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href:
                continue

            absolute = self._normalize_url(urljoin(base_url, href))
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue

            if absolute.startswith(self.allowed_prefix):
                yield CrawlTarget(absolute, self._classify_link(absolute))
                continue

            if self.include_external_tables and parsed.netloc in DEFAULT_EXTERNAL_TABLE_HOSTS:
                yield CrawlTarget(absolute, "table")

    @staticmethod
    def _classify_link(url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        last_segment = path.split("/")[-1].lower()
        if last_segment == "table-of-contents":
            return "toc"
        if last_segment.startswith("chapter-"):
            return "chapter"
        if last_segment in {"summary-of-changes", "quick-reference", "uniform-components"}:
            return "reference"
        return "article"

    @staticmethod
    def _normalize_url(url: str) -> str:
        clean, _fragment = urldefrag(url)
        parsed = urlparse(clean)
        path = parsed.path
        if parsed.netloc.endswith("mynavyhr.navy.mil") and not path.endswith("/"):
            maybe_file = path.split("/")[-1]
            if "." not in maybe_file:
                path = path + "/"
        return parsed._replace(path=path).geturl()

    @staticmethod
    def _clean_text(value: str) -> str:
        return WHITESPACE_RE.sub(" ", value.replace("\xa0", " ")).strip()

    @staticmethod
    def _dedupe_adjacent(lines: Iterable[str]) -> list[str]:
        output: list[str] = []
        previous = None
        for line in lines:
            if line == previous:
                continue
            output.append(line)
            previous = line
        return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-url", default=DEFAULT_START_URL)
    parser.add_argument("--allowed-prefix", default=DEFAULT_ALLOWED_PREFIX)
    parser.add_argument("--output", default="navy_uniforms_context.jsonl")
    parser.add_argument(
        "--include-external-tables",
        action="store_true",
        help="Also crawl table links hosted on mynavyhr.navy.afpims.mil.",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.3,
        help="Delay between requests so the crawl is polite.",
    )
    return parser.parse_args()


def write_jsonl(documents: Iterable[dict], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as handle:
        for document in documents:
            handle.write(json.dumps(document, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    crawler = UniformRegulationsCrawler(
        start_url=args.start_url,
        allowed_prefix=args.allowed_prefix,
        include_external_tables=args.include_external_tables,
        pause_seconds=args.pause_seconds,
    )
    documents = crawler.crawl()
    write_jsonl(documents, args.output)
    print(f"Wrote {len(documents)} documents to {args.output}")


if __name__ == "__main__":
    main()
