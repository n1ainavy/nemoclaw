#!/usr/bin/env python3
"""
Navy Policy Document Downloader v2
====================================
Systematically builds a local repository of US Navy / DoD policy documents.

Sources handled:
  01-RESPERSMAN   navyreserve.navy.mil   (Akamai-protected; curl fallback)
  02-MILPERSMAN   mynavyhr.navy.mil      (Akamai-protected; curl fallback)
  03-SECNAV-INST  secnav.navy.mil        (F5 WAF on listing pages)
  04-BUPERS-INST  mynavyhr.navy.mil      (Akamai-protected)
  05-JTR          travel.dod.mil         (may be network-blocked)
  06-DODD         esd.whs.mil            (may be network-blocked)
  07-DODI         esd.whs.mil            (may be network-blocked)
  08-DODM         esd.whs.mil            (may be network-blocked)
  09-DTM          esd.whs.mil            (may be network-blocked)
  10-CJCSI        jcs.mil                (may be network-blocked)
  11-CJCSM        jcs.mil                (may be network-blocked)
  12-CJCSN        jcs.mil                (may be network-blocked)
  13-NAVREGS      secnav.navy.mil        (F5 WAF)
  14-UNIFORM-REGS mynavyhr.navy.mil      (saved as HTML+TXT for agent context)
  15-CAREER-MGMT  mynavyhr.navy.mil      (recursive crawl, PDF + page capture)

Usage:
  pip install requests beautifulsoup4 lxml
  python3 downloader.py [--sources all] [--output ./output] [--dry-run]
  python3 downloader.py --sources 01,02 --output /data/navy_policy
  python3 downloader.py --sources 03 --brave-key YOUR_KEY   # URL discovery

Outputs:
  output/
    01-RESPERSMAN/             PDFs + HTML pages
    02-MILPERSMAN/
    ...
    index.json                 Machine-readable master index (all documents)
    index.md                   Human-readable index with ✓/⚠ status
    review_required.md         All URLs that need manual download
    download_log.txt           Verbose per-request log

Environment variables:
  BRAVE_API_KEY   Brave Search API key for URL discovery fallback
  GITHUB_TOKEN    Personal access token for auto-push to GitHub
  GITHUB_REPO     owner/repo-name  (e.g. "jdoe/navy-policy-repo")
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse, unquote, quote

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Import known document database
# ---------------------------------------------------------------------------
from known_docs import (
    RESPERSMAN_ARTICLES,
    MILPERSMAN_ARTICLES,
    SECNAVINST_DOCS,
    BUPERSINST_DOCS,
    JTR_DOCS,
    DODD_DOCS,
    DODI_DOCS,
    DODM_DOCS,
    DTM_DOCS,
    CJCSI_DOCS,
    CJCSM_DOCS,
    CJCSN_DOCS,
    UNIFORM_REG_ARTICLES,
    CAREER_MGMT_SECTIONS,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REQUEST_DELAY = 1.5
MAX_RETRIES   = 3
TIMEOUT       = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Domains that may be blocked at the network level in some environments
POTENTIALLY_BLOCKED = {
    "esd.whs.mil", "www.esd.whs.mil",
    "jcs.mil", "www.jcs.mil",
    "travel.dod.mil", "www.travel.dod.mil",
}

# Known WAF-protected listing pages (PDFs accessible but listings blocked)
WAF_LISTING_PAGES = {
    "navyreserve.navy.mil", "www.navyreserve.navy.mil",
    "mynavyhr.navy.mil", "www.mynavyhr.navy.mil",
    "secnav.navy.mil", "www.secnav.navy.mil",
}

log = logging.getLogger("navy_dl")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PolicyDocument:
    source_code: str
    doc_id: str
    title: str
    url: str
    pdf_url: Optional[str] = None
    date_released: str = ""          # e.g. "15 Mar 2022" or "Mar 2022"
    local_path: Optional[str] = None
    downloaded: bool = False
    download_error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def setup_logging(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(output_dir / "download_log.txt", mode="a"),
        ],
    )


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def domain_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def is_network_blocked(url: str) -> bool:
    return domain_of(url) in POTENTIALLY_BLOCKED


def is_waf_listing(url: str) -> bool:
    return domain_of(url) in WAF_LISTING_PAGES


def safe_filename(name: str, ext: str = "") -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = name[:200]
    if ext and not name.endswith(ext):
        name += ext
    return name


def is_real_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


def is_waf_html(content: bytes, status: int) -> bool:
    if status != 200:
        return False
    lower = content[:2048].lower()
    return any(p in lower for p in [
        b"captcha", b"support id", b"request rejected",
        b"access denied", b"are you human",
    ])


def fetch_page(
    session: requests.Session,
    url: str,
    retries: int = MAX_RETRIES,
) -> Optional[str]:
    """Fetch HTML, return text or None on failure/WAF block."""
    for attempt in range(1, retries + 1):
        try:
            time.sleep(REQUEST_DELAY)
            resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
            if resp.status_code == 200:
                if is_waf_html(resp.content, 200):
                    log.debug("WAF block on %s (attempt %d)", url, attempt)
                    return None
                return resp.text
            log.debug("HTTP %s for %s (attempt %d)", resp.status_code, url, attempt)
        except requests.RequestException as exc:
            log.debug("Request error %s: %s (attempt %d)", url, exc, attempt)
        time.sleep(REQUEST_DELAY * attempt)
    return None


def download_pdf(
    session: requests.Session,
    url: str,
    dest: Path,
    retries: int = MAX_RETRIES,
) -> tuple[bool, str]:
    """Download PDF to dest. Returns (success, error_message)."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest.stat().st_size > 2048:
        # Already downloaded and non-trivial size
        return True, ""

    for attempt in range(1, retries + 1):
        try:
            time.sleep(REQUEST_DELAY)
            resp = session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)

            if resp.status_code == 200:
                raw = b"".join(resp.iter_content(8192))
                if is_waf_html(raw, 200):
                    return False, "WAF/CAPTCHA challenge returned instead of PDF"
                if not is_real_pdf(raw):
                    return False, f"Response is not a PDF (got {raw[:20]!r})"
                dest.write_bytes(raw)
                log.info("  ✓ %s (%d KB)", dest.name, len(raw) // 1024)
                return True, ""

            elif resp.status_code in (403, 401):
                return False, f"HTTP {resp.status_code} – access denied (Akamai/WAF)"
            else:
                log.debug("  HTTP %s for %s (attempt %d)", resp.status_code, url, attempt)

        except requests.RequestException as exc:
            log.debug("  Download error %s: %s", url, exc)

        time.sleep(REQUEST_DELAY * attempt)

    return False, "Download failed after retries"


def extract_pdf_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if ".pdf" in href.lower():
            out.append(urljoin(base_url, href))
    return out


def extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.startswith(("#", "javascript:", "mailto:")):
            continue
        out.append((urljoin(base_url, href), tag.get_text(strip=True)))
    return out


# ---------------------------------------------------------------------------
# Brave Search API (URL discovery fallback)
# ---------------------------------------------------------------------------

def brave_search_pdf_urls(query: str, api_key: str, count: int = 20) -> list[str]:
    """Use Brave Search API to find PDF URLs matching a query."""
    if not api_key:
        return []
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count, "search_lang": "en"},
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return [
                r["url"] for r in data.get("web", {}).get("results", [])
                if ".pdf" in r.get("url", "").lower()
            ]
    except Exception as exc:
        log.debug("Brave API error: %s", exc)
    return []


# ---------------------------------------------------------------------------
# GitHub integration
# ---------------------------------------------------------------------------

def push_to_github(output_dir: Path, token: str, repo: str, commit_msg: str = ""):
    """Commit and push output_dir to GitHub."""
    if not token or not repo:
        return
    commit_msg = commit_msg or f"Auto-update Navy policy documents {datetime.utcnow().strftime('%Y-%m-%d')}"
    git_url = f"https://{token}@github.com/{repo}.git"
    try:
        if not (output_dir / ".git").exists():
            subprocess.run(["git", "init"], cwd=output_dir, check=True, capture_output=True)
            subprocess.run(["git", "remote", "add", "origin", git_url], cwd=output_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=output_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=output_dir, check=True, capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=output_dir, check=True, capture_output=True)
        log.info("Pushed to GitHub: %s", repo)
    except subprocess.CalledProcessError as exc:
        log.warning("GitHub push failed: %s", exc)


# ---------------------------------------------------------------------------
# Base scraper
# ---------------------------------------------------------------------------

class BaseScraper:
    source_code: str = ""
    source_name: str = ""
    listing_url: str = ""

    def __init__(
        self,
        session: requests.Session,
        output_dir: Path,
        brave_key: str = "",
        dry_run: bool = False,
    ):
        self.session = session
        self.output_dir = output_dir / self.source_code
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.brave_key = brave_key
        self.dry_run = dry_run
        self.documents: list[PolicyDocument] = []

    def scrape(self) -> list[PolicyDocument]:
        raise NotImplementedError

    # -- helpers ---------------------------------------------------------------

    def _doc(
        self,
        doc_id: str,
        title: str,
        url: str,
        pdf_url: Optional[str] = None,
        date_released: str = "",
    ) -> PolicyDocument:
        return PolicyDocument(
            source_code=self.source_code,
            doc_id=doc_id,
            title=title,
            url=url,
            pdf_url=pdf_url,
            date_released=date_released,
        )

    def _try_download(self, doc: PolicyDocument) -> None:
        """Attempt to download a document's PDF, updating doc in place."""
        if self.dry_run:
            doc.download_error = "dry-run mode"
            return
        if not doc.pdf_url:
            doc.download_error = "No PDF URL available"
            return
        if is_network_blocked(doc.pdf_url):
            doc.download_error = (
                f"Domain {domain_of(doc.pdf_url)} is blocked at the network level — "
                "run curl_downloader.sh on a machine with open internet access"
            )
            return

        fname = safe_filename(doc.doc_id, ".pdf")
        dest = self.output_dir / fname
        ok, err = download_pdf(self.session, doc.pdf_url, dest)
        if ok:
            doc.downloaded = True
            doc.local_path = str(dest.relative_to(dest.parents[2]))
        else:
            doc.download_error = err
            # Try Brave Search as a fallback for URL discovery
            if self.brave_key and "access denied" in err.lower():
                self._brave_fallback(doc)

    def _brave_fallback(self, doc: PolicyDocument) -> None:
        query = f'site:{domain_of(doc.pdf_url or doc.url)} "{doc.doc_id}" filetype:pdf'
        urls = brave_search_pdf_urls(query, self.brave_key)
        for candidate in urls:
            doc.pdf_url = candidate
            fname = safe_filename(doc.doc_id, ".pdf")
            dest = self.output_dir / fname
            ok, err = download_pdf(self.session, candidate, dest)
            if ok:
                doc.downloaded = True
                doc.local_path = str(dest.relative_to(dest.parents[2]))
                doc.download_error = None
                log.info("  ✓ Brave fallback found: %s", candidate)
                return
        doc.download_error += " | Brave fallback also failed"

    def _scrape_listing_page(self, url: str) -> list[str]:
        """Fetch a listing page and return all PDF URLs found."""
        html = fetch_page(self.session, url)
        if not html:
            return []
        return extract_pdf_links(html, url)

    def _queue_blocked(self, doc_id: str, title: str, listing_url: str, pdf_url: str, reason: str) -> PolicyDocument:
        doc = self._doc(doc_id, title, listing_url, pdf_url)
        doc.download_error = reason
        return doc


# ===========================================================================
# 01 – RESPERSMAN
# ===========================================================================

class RespersmanScraper(BaseScraper):
    source_code = "01-RESPERSMAN"
    source_name = "Reserve Personnel Manual (RESPERSMAN)"
    listing_url = "https://www.navyreserve.navy.mil/Resources/Official-RESFOR-Guidance/RESPERSMAN/"

    # DNN portal path patterns used by navyreserve.navy.mil
    PDF_BASES = [
        "https://www.navyreserve.navy.mil/Portals/37/Documents/RESPERSMAN",
        "https://www.navyreserve.navy.mil/Portals/37/Documents",
        "https://www.navyreserve.navy.mil/Portals/37/RESPERSMAN",
    ]

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)

        # 1. Try live listing page
        pdf_urls = self._scrape_listing_page(self.listing_url)
        if pdf_urls:
            log.info("  Live listing: %d PDFs found", len(pdf_urls))
            for url in pdf_urls:
                doc_id = unquote(url.rsplit("/", 1)[-1]).replace(".pdf", "").replace(".PDF", "")
                doc = self._doc(doc_id, doc_id, url, url)
                self._try_download(doc)
                self.documents.append(doc)
        else:
            log.info("  Listing blocked — probing known article URL patterns")

        # 2. Build from known article list (fills gaps regardless)
        existing_ids = {d.doc_id for d in self.documents}
        for article_num, title, date_released in RESPERSMAN_ARTICLES:
            doc_id = f"RESPERSMAN {article_num}"
            if doc_id in existing_ids:
                continue

            chapter = article_num.split("-")[0]
            # Try each base path pattern
            pdf_url = None
            for base in self.PDF_BASES:
                candidate = f"{base}/{chapter}/RESPERSMAN-{article_num}.pdf"
                pdf_url = candidate
                break  # Use first pattern; _try_download will probe alternates

            doc = self._doc(doc_id, title, self.listing_url, pdf_url, date_released)

            # Try multiple URL patterns per article
            if not self.dry_run and pdf_url:
                candidates = [
                    f"{self.PDF_BASES[0]}/{chapter}/RESPERSMAN-{article_num}.pdf",
                    f"{self.PDF_BASES[0]}/RESPERSMAN-{article_num}.pdf",
                    f"https://www.navyreserve.navy.mil/Portals/37/Documents/RESPERSMAN/RESPERSMAN-{article_num}.pdf",
                ]
                for c in candidates:
                    doc.pdf_url = c
                    fname = safe_filename(doc_id, ".pdf")
                    dest = self.output_dir / fname
                    ok, err = download_pdf(self.session, c, dest)
                    if ok:
                        doc.downloaded = True
                        doc.local_path = str(dest.relative_to(dest.parents[2]))
                        break
                    doc.download_error = err

                if not doc.downloaded and "access denied" not in (doc.download_error or ""):
                    # Might be a 404 — URL pattern wrong, queue for review
                    doc.download_error = (
                        f"URL pattern not found for {article_num}. "
                        f"Listing page: {self.listing_url}"
                    )

            self.documents.append(doc)

        log.info("  Total RESPERSMAN entries: %d", len(self.documents))
        return self.documents


# ===========================================================================
# 02 – MILPERSMAN
# ===========================================================================

class MilpersmanScraper(BaseScraper):
    source_code = "02-MILPERSMAN"
    source_name = "Military Personnel Manual (MILPERSMAN)"
    listing_url = "https://www.mynavyhr.navy.mil/References/MILPERSMAN/"

    PDF_BASES = [
        "https://www.mynavyhr.navy.mil/Portals/55/Reference/MILPERSMAN",
        "https://www.mynavyhr.navy.mil/Portals/55/Documents/Career/MILPERSMAN",
        "https://www.mynavyhr.navy.mil/Portals/55/References/MILPERSMAN",
    ]

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)

        # 1. Try live scrape
        pdf_urls = self._scrape_listing_page(self.listing_url)
        if pdf_urls:
            for url in pdf_urls:
                doc_id = unquote(url.rsplit("/", 1)[-1]).replace(".pdf", "")
                doc = self._doc(doc_id, doc_id, url, url)
                self._try_download(doc)
                self.documents.append(doc)

            # Also follow sub-section links
            html = fetch_page(self.session, self.listing_url)
            if html:
                for sub_url, _ in extract_links(html, self.listing_url):
                    if "milpersman" in sub_url.lower() and sub_url != self.listing_url:
                        sub_pdfs = self._scrape_listing_page(sub_url)
                        for pdf_url in sub_pdfs:
                            doc_id = unquote(pdf_url.rsplit("/", 1)[-1]).replace(".pdf", "")
                            if doc_id not in {d.doc_id for d in self.documents}:
                                doc = self._doc(doc_id, doc_id, pdf_url, pdf_url)
                                self._try_download(doc)
                                self.documents.append(doc)
        else:
            log.info("  Listing blocked — using known article database")

        # 2. Known article stubs
        existing_ids = {d.doc_id for d in self.documents}
        for article_num, title, date_released in MILPERSMAN_ARTICLES:
            doc_id = f"MILPERSMAN {article_num}"
            if doc_id in existing_ids:
                continue
            chapter = article_num.split("-")[0]
            candidates = [
                f"{self.PDF_BASES[0]}/{chapter}/{article_num}.pdf",
                f"{self.PDF_BASES[0]}/{article_num}.pdf",
                f"https://www.mynavyhr.navy.mil/Portals/55/Reference/MILPERSMAN/MILPERSMAN-{article_num}.pdf",
            ]
            doc = self._doc(doc_id, title, self.listing_url, candidates[0], date_released)
            if not self.dry_run:
                for c in candidates:
                    doc.pdf_url = c
                    dest = self.output_dir / safe_filename(doc_id, ".pdf")
                    ok, err = download_pdf(self.session, c, dest)
                    if ok:
                        doc.downloaded = True
                        doc.local_path = str(dest.relative_to(dest.parents[2]))
                        break
                    doc.download_error = err
            self.documents.append(doc)

        log.info("  Total MILPERSMAN entries: %d", len(self.documents))
        return self.documents


# ===========================================================================
# 03 – SECNAV INSTRUCTIONS / MANUALS
# ===========================================================================

class SecnavInstScraper(BaseScraper):
    source_code = "03-SECNAV-INST"
    source_name = "SECNAV Instructions & Manuals"
    listing_url = "https://www.secnav.navy.mil/doni/default.aspx"

    # DONI uses a folder structure: /doni/Directives/NNNNN <Section Title>/...
    # The numeric prefix maps to instruction series
    SERIES_FOLDERS = {
        "1": "01000%20Military%20Personnel%20Support",
        "2": "02000%20Military%20Personnel",
        "3": "03000%20Naval%20Operations%20and%20Readiness",
        "4": "04000%20Logistics",
        "5": "05000%20General%20Management%20and%20Organization",
        "7": "07000%20Financial%20Management",
    }

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)

        # 1. Try listing pages
        for page in ["manuals-secnav.aspx", "navyinstructions.aspx", "alldirectives.aspx"]:
            pdf_urls = self._scrape_listing_page(
                f"https://www.secnav.navy.mil/doni/{page}"
            )
            for url in pdf_urls:
                doc_id = unquote(url.rsplit("/", 1)[-1]).replace(".pdf", "")
                if doc_id not in {d.doc_id for d in self.documents}:
                    doc = self._doc(doc_id, doc_id, url, url)
                    self._try_download(doc)
                    self.documents.append(doc)

        # 2. Probe known numbers
        existing_ids = {d.doc_id for d in self.documents}
        for num, title, date_released in SECNAVINST_DOCS:
            # Determine if it's an instruction, notice, or manual
            if num.startswith("M-"):
                prefix = "SECNAV M"
                doc_type = "Manual"
            else:
                prefix = "SECNAVINST"
                doc_type = "Instruction"

            doc_id = f"{prefix} {num}"
            if doc_id in existing_ids:
                continue

            series_key = num[0]
            folder = self.SERIES_FOLDERS.get(series_key, "")
            candidates = []
            if folder:
                candidates.append(
                    f"https://www.secnav.navy.mil/doni/Directives/{folder}/{num.replace('-', '%20')}.pdf"
                )
            candidates += [
                f"https://www.secnav.navy.mil/doni/Instructions/{num}.pdf",
                f"https://www.secnav.navy.mil/doni/Issuances/{num}.pdf",
                f"https://www.secnav.navy.mil/doni/{doc_type}s/{num}.pdf",
            ]

            doc = self._doc(doc_id, title, self.listing_url, candidates[0], date_released)

            if not self.dry_run:
                for c in candidates:
                    doc.pdf_url = c
                    dest = self.output_dir / safe_filename(doc_id, ".pdf")
                    ok, err = download_pdf(self.session, c, dest)
                    if ok:
                        doc.downloaded = True
                        doc.local_path = str(dest.relative_to(dest.parents[2]))
                        break
                    doc.download_error = err
                if not doc.downloaded:
                    doc.download_error = (
                        "WAF blocks direct PDF access. Manual download: "
                        "https://www.secnav.navy.mil/doni/"
                    )

            self.documents.append(doc)

        log.info("  Total SECNAV entries: %d", len(self.documents))
        return self.documents


# ===========================================================================
# 04 – BUPERS INSTRUCTIONS
# ===========================================================================

class BupersInstScraper(BaseScraper):
    source_code = "04-BUPERS-INST"
    source_name = "BUPERS Instructions (BUPERSINST)"
    listing_url = "https://www.mynavyhr.navy.mil/References/BUPERS-Instructions/"

    PDF_BASES = [
        "https://www.mynavyhr.navy.mil/Portals/55/Reference/Instructions/BUPERSINST",
        "https://www.mynavyhr.navy.mil/Portals/55/Reference/Instructions",
        "https://www.mynavyhr.navy.mil/Portals/55/Documents/bupers/Instructions",
    ]

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)

        # Try live listing
        html = fetch_page(self.session, self.listing_url)
        if html:
            for pdf_url in extract_pdf_links(html, self.listing_url):
                doc_id = unquote(pdf_url.rsplit("/", 1)[-1]).replace(".pdf", "")
                doc = self._doc(doc_id, doc_id, pdf_url, pdf_url)
                self._try_download(doc)
                self.documents.append(doc)

        # Known list
        existing_ids = {d.doc_id for d in self.documents}
        for num, title, date_released in BUPERSINST_DOCS:
            doc_id = f"BUPERSINST {num}"
            if doc_id in existing_ids:
                continue
            candidates = [f"{base}/{num}.pdf" for base in self.PDF_BASES]
            doc = self._doc(doc_id, title, self.listing_url, candidates[0], date_released)
            if not self.dry_run:
                for c in candidates:
                    doc.pdf_url = c
                    dest = self.output_dir / safe_filename(doc_id, ".pdf")
                    ok, err = download_pdf(self.session, c, dest)
                    if ok:
                        doc.downloaded = True
                        doc.local_path = str(dest.relative_to(dest.parents[2]))
                        break
                    doc.download_error = err
            self.documents.append(doc)

        log.info("  Total BUPERS entries: %d", len(self.documents))
        return self.documents


# ===========================================================================
# Generic "blocked domain" scrapers for 05–12
# ===========================================================================

@dataclass
class BlockedSourceConfig:
    source_code: str
    source_name: str
    listing_url: str
    prefix: str
    known_docs: list
    pdf_base: str = ""


BLOCKED_SOURCES = [
    BlockedSourceConfig(
        "05-JTR", "Joint Travel Regulations (JTR)",
        "https://www.travel.dod.mil/Policy-Regulations/Joint-Travel-Regulations/",
        "JTR",
        JTR_DOCS,
        "https://www.travel.dod.mil/Portals/119/Documents/JTR",
    ),
    BlockedSourceConfig(
        "06-DODD", "DoD Directives (DoDD)",
        "https://www.esd.whs.mil/Directives/issuances/dodd/",
        "DoDD", DODD_DOCS,
        "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodd",
    ),
    BlockedSourceConfig(
        "07-DODI", "DoD Instructions (DoDI)",
        "https://www.esd.whs.mil/Directives/issuances/dodi/",
        "DoDI", DODI_DOCS,
        "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi",
    ),
    BlockedSourceConfig(
        "08-DODM", "DoD Manuals (DoDM)",
        "https://www.esd.whs.mil/Directives/issuances/dodm/",
        "DoDM", DODM_DOCS,
        "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodm",
    ),
    BlockedSourceConfig(
        "09-DTM", "Directive Type Memoranda (DTM)",
        "https://www.esd.whs.mil/DD/DoD-Issuances/DTM/",
        "DTM", DTM_DOCS,
        "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/DTM",
    ),
    BlockedSourceConfig(
        "10-CJCSI", "CJCS Instructions (CJCSI)",
        "https://www.jcs.mil/library/cjcs-instructions/",
        "CJCSI", CJCSI_DOCS,
        "https://www.jcs.mil/Portals/36/Documents/Library/Instructions",
    ),
    BlockedSourceConfig(
        "11-CJCSM", "CJCS Manuals (CJCSM)",
        "https://www.jcs.mil/Library/CJCS-Manuals/",
        "CJCSM", CJCSM_DOCS,
        "https://www.jcs.mil/Portals/36/Documents/Library/Manuals",
    ),
    BlockedSourceConfig(
        "12-CJCSN", "CJCS Notices (CJCSN)",
        "https://www.jcs.mil/Library/CJCS-Notices/",
        "CJCSN", CJCSN_DOCS,
        "https://www.jcs.mil/Portals/36/Documents/Library/Notices",
    ),
]


class BlockedDomainScraper(BaseScraper):
    def __init__(self, config: BlockedSourceConfig, session, output_dir, brave_key="", dry_run=False):
        self.source_code = config.source_code
        self.source_name = config.source_name
        self.listing_url = config.listing_url
        self.prefix = config.prefix
        self.known = config.known_docs
        self.pdf_base = config.pdf_base
        super().__init__(session, output_dir, brave_key, dry_run)

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)
        blocked = is_network_blocked(self.listing_url)

        # Try live scrape even for blocked domains — may work on open internet
        if not blocked:
            pdf_urls = self._scrape_listing_page(self.listing_url)
            for url in pdf_urls:
                doc_id = unquote(url.rsplit("/", 1)[-1]).replace(".pdf", "")
                doc = self._doc(doc_id, doc_id, url, url)
                self._try_download(doc)
                self.documents.append(doc)

        # Known list
        existing_ids = {d.doc_id for d in self.documents}
        for num, title, date_released in self.known:
            doc_id = f"{self.prefix} {num}" if not num.startswith(self.prefix) else num
            if doc_id in existing_ids:
                continue
            # Build likely PDF URL from base path
            safe_num = num.replace(" ", "_").replace("-", "-")
            pdf_url = f"{self.pdf_base}/{safe_num}.pdf" if self.pdf_base else None
            doc = self._doc(doc_id, title, self.listing_url, pdf_url, date_released)

            if blocked or self.dry_run:
                doc.download_error = (
                    f"{domain_of(self.listing_url)} is blocked in this environment. "
                    f"Run curl_downloader.sh on an unrestricted machine. "
                    f"Direct listing: {self.listing_url}"
                )
            else:
                self._try_download(doc)

            self.documents.append(doc)

        log.info("  %s: %d entries (%d blocked)", self.source_name,
                 len(self.documents), sum(1 for d in self.documents if d.download_error))
        return self.documents


# ===========================================================================
# 13 – NAVY REGULATIONS
# ===========================================================================

class NavRegsScraper(BaseScraper):
    source_code = "13-NAVREGS"
    source_name = "United States Navy Regulations"
    listing_url = "https://www.secnav.navy.mil/doni/navyregs.aspx"

    KNOWN = [
        ("NAVREGS-1990",
         "United States Navy Regulations, 1990 (as amended)",
         "https://www.secnav.navy.mil/doni/Regulations/US%20Navy%20Regulations%201990.pdf",
         "14 Sep 1990"),
        ("NAVREGS-CHAPTER-1",
         "NavRegs Chapter 1 – Authority and Responsibility of the Department of the Navy",
         None,
         ""),
    ]

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)
        html = fetch_page(self.session, self.listing_url)
        if html:
            for url in extract_pdf_links(html, self.listing_url):
                doc_id = unquote(url.rsplit("/", 1)[-1]).replace(".pdf", "")
                doc = self._doc(doc_id, doc_id, url, url)
                self._try_download(doc)
                self.documents.append(doc)

        existing_ids = {d.doc_id for d in self.documents}
        for doc_id, title, pdf_url, date_released in self.KNOWN:
            if doc_id in existing_ids:
                continue
            doc = self._doc(doc_id, title, self.listing_url, pdf_url, date_released)
            if pdf_url:
                self._try_download(doc)
            else:
                doc.download_error = "URL not determined — check listing page"
            self.documents.append(doc)

        return self.documents


# ===========================================================================
# 14 – UNIFORM REGULATIONS
# ===========================================================================

class UniformRegsScraper(BaseScraper):
    """
    Saves each Uniform Regulations article as HTML + plain text for LLM context.
    Also downloads any PDFs linked within articles.
    Combines all articles into a single context file.
    """
    source_code = "14-UNIFORM-REGS"
    source_name = "Navy Uniform Regulations"
    toc_url = "https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/Table-of-Contents/"
    base_url = "https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/"

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)
        context_parts: list[str] = []

        html = fetch_page(self.session, self.toc_url)
        if html:
            links = [
                (url, text) for url, text in extract_links(html, self.toc_url)
                if "uniform-regulation" in url.lower()
                and url != self.toc_url
            ]
        else:
            log.info("  TOC blocked — using known article list")
            links = [
                (f"{self.base_url}{slug}/", title)
                for slug, title in UNIFORM_REG_ARTICLES
            ]

        log.info("  Processing %d uniform regulation articles", len(links))

        for url, title in links:
            doc_id = safe_filename(url.rstrip("/").rsplit("/", 1)[-1] or title)
            doc = self._doc(doc_id, title or doc_id, url)

            article_html = fetch_page(self.session, url)
            if article_html and not self.dry_run:
                soup = BeautifulSoup(article_html, "lxml")
                text = soup.get_text(separator="\n", strip=True)

                html_file = self.output_dir / f"{doc_id}.html"
                txt_file  = self.output_dir / f"{doc_id}.txt"
                html_file.write_text(article_html, encoding="utf-8")
                txt_file.write_text(text, encoding="utf-8")

                context_parts.append(f"\n\n## {title}\nSource: {url}\n\n{text}")
                doc.downloaded = True
                doc.local_path = str(html_file.relative_to(html_file.parents[2]))

                # Download PDFs within the article
                for pdf_url in extract_pdf_links(article_html, url):
                    pdf_id = safe_filename(unquote(pdf_url.rsplit("/", 1)[-1]).replace(".pdf", ""))
                    pdf_doc = self._doc(pdf_id, pdf_id, pdf_url, pdf_url)
                    self._try_download(pdf_doc)
                    self.documents.append(pdf_doc)
            else:
                doc.download_error = "Article page blocked (Akamai 403)"

            self.documents.append(doc)

        # Write combined context file
        if context_parts and not self.dry_run:
            combined = "\n".join([
                "# Navy Uniform Regulations – Combined Context",
                f"# Generated: {datetime.now(timezone.utc).isoformat()}",
                "# Source: https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/",
                "",
            ] + context_parts)
            ctx_file = self.output_dir / "_COMBINED_CONTEXT.txt"
            ctx_file.write_text(combined, encoding="utf-8")
            log.info("  Combined context file: %s (%d chars)", ctx_file.name, len(combined))

        log.info("  Total Uniform Reg entries: %d", len(self.documents))
        return self.documents


# ===========================================================================
# 15 – CAREER MANAGEMENT
# ===========================================================================

class CareerMgmtScraper(BaseScraper):
    source_code = "15-CAREER-MGMT"
    source_name = "MyNavyHR Career Management"
    root_url = "https://www.mynavyhr.navy.mil/Career-Management/"
    MAX_DEPTH = 3

    def scrape(self) -> list[PolicyDocument]:
        log.info("=== %s ===", self.source_name)
        visited: set[str] = set()

        # Start with known sections for guaranteed coverage
        for path, title in CAREER_MGMT_SECTIONS:
            url = f"https://www.mynavyhr.navy.mil/{path}"
            self._crawl(url, depth=0, visited=visited, title=title)

        log.info("  Total Career-Management entries: %d", len(self.documents))
        return self.documents

    def _crawl(self, url: str, depth: int, visited: set, title: str = ""):
        if url in visited or depth > self.MAX_DEPTH:
            return
        visited.add(url)

        parsed = urlparse(url)
        if parsed.hostname not in ("www.mynavyhr.navy.mil", "mynavyhr.navy.mil"):
            return
        if "/Career-Management/" not in parsed.path and depth > 0:
            return

        html = fetch_page(self.session, url)
        page_id = safe_filename(
            parsed.path.strip("/").replace("/", "_") or "career_home"
        )

        if not html:
            doc = self._doc(page_id, title or url, url)
            doc.download_error = "Page blocked (Akamai 403)"
            self.documents.append(doc)
            return

        # Save page
        if not self.dry_run:
            html_file = self.output_dir / f"{page_id}.html"
            txt_file  = self.output_dir / f"{page_id}.txt"
            if not html_file.exists():
                html_file.write_text(html, encoding="utf-8")
                soup = BeautifulSoup(html, "lxml")
                txt_file.write_text(soup.get_text(separator="\n", strip=True), encoding="utf-8")

        page_doc = self._doc(page_id, title or f"Career Management: {parsed.path}", url)
        if not self.dry_run:
            page_doc.downloaded = True
            page_doc.local_path = str(
                (self.output_dir / f"{page_id}.html").relative_to(
                    (self.output_dir / f"{page_id}.html").parents[2]
                )
            )
        self.documents.append(page_doc)

        # PDFs on this page
        for pdf_url in extract_pdf_links(html, url):
            if pdf_url not in visited:
                visited.add(pdf_url)
                pdf_id = safe_filename(
                    unquote(pdf_url.rsplit("/", 1)[-1]).replace(".pdf", "")
                )
                pdf_doc = self._doc(pdf_id, pdf_id, pdf_url, pdf_url)
                self._try_download(pdf_doc)
                self.documents.append(pdf_doc)

        # Recurse into sub-links
        if depth < self.MAX_DEPTH:
            for sub_url, sub_title in extract_links(html, url):
                self._crawl(sub_url, depth + 1, visited, sub_title)


# ===========================================================================
# Output writers
# ===========================================================================

def write_json_index(docs: list[PolicyDocument], out: Path):
    downloaded = [d for d in docs if d.downloaded]
    pending = [d for d in docs if not d.downloaded]
    by_source: dict[str, list] = {}
    for d in docs:
        by_source.setdefault(d.source_code, []).append(d.to_dict())

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(docs),
            "downloaded": len(downloaded),
            "pending_review": len(pending),
        },
        "by_source": {src: {"count": len(items), "documents": items}
                      for src, items in sorted(by_source.items())},
    }
    path = out / "index.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("index.json → %d total docs", len(docs))


def write_md_index(docs: list[PolicyDocument], out: Path):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Navy Policy Document Index",
        f"_Generated: {ts}_\n",
        f"| Stat | Count |",
        f"|------|-------|",
        f"| Total documents | {len(docs)} |",
        f"| Downloaded ✓ | {sum(1 for d in docs if d.downloaded)} |",
        f"| Pending review ⚠ | {sum(1 for d in docs if not d.downloaded)} |",
        "",
        "---",
        "",
    ]
    by_source: dict[str, list[PolicyDocument]] = {}
    for d in docs:
        by_source.setdefault(d.source_code, []).append(d)

    for src, items in sorted(by_source.items()):
        dl = sum(1 for d in items if d.downloaded)
        lines += [
            f"## {src}",
            f"_{dl}/{len(items)} downloaded_",
            "",
            "| | Doc ID | Title | Date | Link |",
            "|--|--------|-------|------|------|",
        ]
        for d in items:
            icon  = "✓" if d.downloaded else "⚠"
            title = d.title.replace("|", "\\|")[:60]
            date  = d.date_released or "—"
            link_url = d.pdf_url or d.url
            lines.append(f"| {icon} | `{d.doc_id}` | {title} | {date} | [→]({link_url}) |")
        lines.append("")

    (out / "index.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("index.md written")


def write_review_file(docs: list[PolicyDocument], out: Path):
    pending = [d for d in docs if not d.downloaded]
    by_source: dict[str, list[PolicyDocument]] = {}
    for d in pending:
        by_source.setdefault(d.source_code, []).append(d)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Documents Requiring Manual Download",
        f"_Generated: {ts}_",
        f"_Total pending: {len(pending)}_",
        "",
        "> These documents could not be auto-downloaded. Download manually and",
        "> place in the corresponding folder, then re-run the script to update the index.",
        "",
        "---",
        "",
    ]
    for src, items in sorted(by_source.items()):
        lines += [f"## {src} ({len(items)} pending)", ""]
        for d in items:
            lines.append(f"### {d.doc_id}")
            lines.append(f"- **Title:** {d.title}")
            lines.append(f"- **Listing page:** <{d.url}>")
            if d.pdf_url:
                lines.append(f"- **PDF URL:** <{d.pdf_url}>")
            if d.download_error:
                lines.append(f"- **Reason:** _{d.download_error}_")
            lines.append("")

    (out / "review_required.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("review_required.md → %d pending", len(pending))


# ---------------------------------------------------------------------------
# SOURCE METADATA — human-readable names and listing URLs for the report
# ---------------------------------------------------------------------------

SOURCE_META = {
    "01-RESPERSMAN": {
        "name": "Reserve Personnel Manual (RESPERSMAN)",
        "listing": "https://www.navyreserve.navy.mil/Resources/Official-RESFOR-Guidance/RESPERSMAN/",
        "authority": "Commander, Navy Reserve Forces Command (CNRFC)",
        "description": "Policies and procedures governing the administration of Navy Reserve personnel.",
    },
    "02-MILPERSMAN": {
        "name": "Military Personnel Manual (MILPERSMAN)",
        "listing": "https://www.mynavyhr.navy.mil/References/MILPERSMAN/",
        "authority": "Bureau of Naval Personnel (BUPERS)",
        "description": "Primary reference for Navy enlisted and officer personnel policy.",
    },
    "03-SECNAV-INST": {
        "name": "SECNAV Instructions & Manuals",
        "listing": "https://www.secnav.navy.mil/doni/default.aspx",
        "authority": "Secretary of the Navy (SECNAV)",
        "description": "Directives and manuals issued by the Secretary of the Navy.",
    },
    "04-BUPERS-INST": {
        "name": "BUPERS Instructions (BUPERSINST)",
        "listing": "https://www.mynavyhr.navy.mil/References/BUPERS-Instructions/",
        "authority": "Bureau of Naval Personnel (BUPERS)",
        "description": "Administrative instructions issued by the Chief of Naval Personnel.",
    },
    "05-JTR": {
        "name": "Joint Travel Regulations (JTR)",
        "listing": "https://www.travel.dod.mil/Policy-Regulations/Joint-Travel-Regulations/",
        "authority": "Under Secretary of Defense (Comptroller)",
        "description": "Governs travel and transportation allowances for uniformed service members.",
    },
    "06-DODD": {
        "name": "DoD Directives (DoDD)",
        "listing": "https://www.esd.whs.mil/Directives/issuances/dodd/",
        "authority": "Office of the Secretary of Defense (OSD)",
        "description": "High-level DoD policy documents that establish or describe policy, programs, and organizational relationships.",
    },
    "07-DODI": {
        "name": "DoD Instructions (DoDI)",
        "listing": "https://www.esd.whs.mil/Directives/issuances/dodi/",
        "authority": "Office of the Secretary of Defense (OSD)",
        "description": "Implements the policy in DoD Directives and prescribes detailed procedures.",
    },
    "08-DODM": {
        "name": "DoD Manuals (DoDM)",
        "listing": "https://www.esd.whs.mil/Directives/issuances/dodm/",
        "authority": "Office of the Secretary of Defense (OSD)",
        "description": "Provides detailed procedures implementing DoD policy directives and instructions.",
    },
    "09-DTM": {
        "name": "Directive Type Memoranda (DTM)",
        "listing": "https://www.esd.whs.mil/DD/DoD-Issuances/DTM/",
        "authority": "Office of the Secretary of Defense (OSD)",
        "description": "Interim policy documents that expire or are converted to permanent issuances.",
    },
    "10-CJCSI": {
        "name": "CJCS Instructions (CJCSI)",
        "listing": "https://www.jcs.mil/library/cjcs-instructions/",
        "authority": "Chairman, Joint Chiefs of Staff (CJCS)",
        "description": "Implements joint policy and provides procedural guidance for the Armed Forces.",
    },
    "11-CJCSM": {
        "name": "CJCS Manuals (CJCSM)",
        "listing": "https://www.jcs.mil/Library/CJCS-Manuals/",
        "authority": "Chairman, Joint Chiefs of Staff (CJCS)",
        "description": "Detailed procedural guidance supporting CJCS Instructions.",
    },
    "12-CJCSN": {
        "name": "CJCS Notices (CJCSN)",
        "listing": "https://www.jcs.mil/Library/CJCS-Notices/",
        "authority": "Chairman, Joint Chiefs of Staff (CJCS)",
        "description": "One-time or short-term issuances announcing policy changes or events.",
    },
    "13-NAVREGS": {
        "name": "United States Navy Regulations",
        "listing": "https://www.secnav.navy.mil/doni/navyregs.aspx",
        "authority": "Secretary of the Navy (SECNAV)",
        "description": "The primary legal document of the Department of the Navy, prescribing the organization, duties, responsibilities, and authority of naval commands.",
    },
    "14-UNIFORM-REGS": {
        "name": "Navy Uniform Regulations",
        "listing": "https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/Table-of-Contents/",
        "authority": "Chief of Naval Personnel (CNP)",
        "description": "Prescribes the authorized uniforms and grooming standards for Navy personnel.",
    },
    "15-CAREER-MGMT": {
        "name": "MyNavyHR Career Management",
        "listing": "https://www.mynavyhr.navy.mil/Career-Management/",
        "authority": "Bureau of Naval Personnel (BUPERS)",
        "description": "Centralized career management resources for enlisted and officer Navy personnel.",
    },
}


def write_policy_report(
    docs: list[PolicyDocument],
    out: Path,
    sources_run: list[str],
    report_file: str = "policy_report.md",
) -> None:
    """
    Generate a comprehensive policy document report in Markdown.

    The report is organised by source and contains one row per document with:
      Source | Doc Number | Title | Date Released | Download Link

    Parameters
    ----------
    docs         : Full document list from all scrapers.
    out          : Output directory where the file is written.
    sources_run  : Ordered list of source codes actually processed this run
                   (determines section order and completeness note).
    report_file  : Output filename (default: policy_report.md).
    """
    now_utc = datetime.now(timezone.utc)
    timestamp_display = now_utc.strftime("%d %B %Y  %H:%M UTC")
    timestamp_iso     = now_utc.isoformat()

    # Group docs by their full source_code (e.g. "05-JTR", "06-DODD").
    # sources_run contains 2-digit prefixes like ["05", "06"], so we match by prefix
    # to build an ordered list of the actual source_code keys.
    by_source: dict[str, list[PolicyDocument]] = {}
    for d in docs:
        by_source.setdefault(d.source_code, []).append(d)

    # Ordered list of full source_code values, following the sources_run order
    ordered_sources: list[str] = []
    for num in sources_run:
        for key in sorted(by_source):
            if key.startswith(num) and key not in ordered_sources:
                ordered_sources.append(key)
    # Safety: include anything not already covered
    for key in sorted(by_source):
        if key not in ordered_sources:
            ordered_sources.append(key)

    total      = len(docs)
    with_dates = sum(1 for d in docs if d.date_released and d.date_released != "Periodic")
    with_links = sum(1 for d in docs if d.pdf_url or d.url)

    lines: list[str] = [
        "# Navy / DoD Policy Document Report",
        "",
        f"> **Report generated:** {timestamp_display}  ",
        f"> **ISO timestamp:** `{timestamp_iso}`  ",
        f"> **Sources included:** {', '.join(ordered_sources)}  ",
        f"> **Total documents:** {total}  ",
        f"> **Documents with release date:** {with_dates}  ",
        f"> **Documents with download link:** {with_links}  ",
        "",
        "> _This report is generated automatically from known document databases and live_",
        "> _scraping where accessible. Release dates reflect the most recent version on record._",
        "> _Run `python3 downloader.py --report` to regenerate with the latest data._",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]

    # TOC entries — one line per source section
    for src in ordered_sources:
        meta = SOURCE_META.get(src, {})
        src_name = meta.get("name", src)
        count = len(by_source.get(src, []))
        # GitHub-compatible anchor: lowercase, hyphens, no special chars
        anchor = src.lower().replace(" ", "-").replace("/", "").replace("(", "").replace(")", "")
        lines.append(f"- [{src} – {src_name}](#{anchor}) _{count} documents_")

    lines += ["", "---", ""]

    # One section per source
    for src in ordered_sources:
        items = by_source.get(src, [])
        meta  = SOURCE_META.get(src, {})
        src_name    = meta.get("name", src)
        authority   = meta.get("authority", "")
        description = meta.get("description", "")
        listing_url = meta.get("listing", "")

        # Section header
        lines += [
            f"## {src} – {src_name}",
            "",
        ]
        if authority:
            lines.append(f"**Issuing Authority:** {authority}  ")
        if listing_url:
            lines.append(f"**Official Listing:** <{listing_url}>  ")
        if description:
            lines.append(f"**Scope:** {description}  ")
        lines += [
            f"**Documents in this section:** {len(items)}  ",
            "",
        ]

        if not items:
            lines += [
                "_No documents were indexed for this source in this run._",
                "",
                "---",
                "",
            ]
            continue

        # Table header
        lines += [
            "| # | Document Number | Title | Date Released | Download |",
            "|---|----------------|-------|--------------|----------|",
        ]

        for i, doc in enumerate(items, 1):
            # Escape pipe characters in title
            title = doc.title.replace("|", "\\|")

            # Truncate very long titles for readability
            display_title = (title[:72] + "…") if len(title) > 75 else title

            # Date field
            date = doc.date_released.strip() if doc.date_released else "—"

            # Download link — prefer PDF URL, fall back to listing page URL
            link_url = doc.pdf_url or doc.url or ""
            if link_url:
                download_cell = f"[PDF]({link_url})" if doc.pdf_url else f"[Listing]({link_url})"
            else:
                download_cell = "—"

            lines.append(
                f"| {i} | `{doc.doc_id}` | {display_title} | {date} | {download_cell} |"
            )

        lines += ["", "---", ""]

    # Footer
    lines += [
        "## Notes",
        "",
        "- **Date Released** reflects the publication or most recent revision date of the "
        "current version. Dates marked `—` were not available in the known document database "
        "and should be verified at the official listing page.",
        "- **Periodic** indicates issuances published on a recurring schedule with no fixed date.",
        "- Download links point to the best-known PDF URL. If a link returns a 403 or WAF "
        "challenge, access the document through the official listing page listed in each section.",
        "- Sources 05 (JTR), 06–09 (DoD issuances), and 10–12 (CJCS issuances) may require "
        "access from an unrestricted network. Use `curl_downloader.sh` for automated download.",
        "- To regenerate this report after adding new documents to `known_docs.py`:",
        "  ```bash",
        "  python3 downloader.py --report --dry-run --output ./output",
        "  ```",
        "",
        f"_Report ends — generated {timestamp_display}_",
    ]

    report_path = out / report_file
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(
        "Policy report written: %s (%d documents, %d sections)",
        report_path.name, total, len(sources_run),
    )


# ===========================================================================
# Main
# ===========================================================================

def build_scrapers(
    session: requests.Session,
    output_dir: Path,
    brave_key: str,
    dry_run: bool,
    selected: list[str],
) -> list[BaseScraper]:
    scrapers = []
    kwargs = dict(session=session, output_dir=output_dir, brave_key=brave_key, dry_run=dry_run)

    mapping = {
        "01": lambda: RespersmanScraper(**kwargs),
        "02": lambda: MilpersmanScraper(**kwargs),
        "03": lambda: SecnavInstScraper(**kwargs),
        "04": lambda: BupersInstScraper(**kwargs),
        "13": lambda: NavRegsScraper(**kwargs),
        "14": lambda: UniformRegsScraper(**kwargs),
        "15": lambda: CareerMgmtScraper(**kwargs),
    }
    # Blocked-domain sources
    for cfg in BLOCKED_SOURCES:
        src_num = cfg.source_code[:2]
        mapping[src_num] = lambda c=cfg: BlockedDomainScraper(c, **kwargs)

    for num in selected:
        if num in mapping:
            scrapers.append(mapping[num]())
        else:
            log.warning("Unknown source number: %s", num)
    return scrapers


def main():
    parser = argparse.ArgumentParser(
        description="Navy Policy Document Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--sources", default="all",
        help="Comma-separated source numbers (01-15) or 'all'")
    parser.add_argument("--output", default="./output",
        help="Output directory (default: ./output)")
    parser.add_argument("--dry-run", action="store_true",
        help="Build index and report without downloading files")
    parser.add_argument("--report", action="store_true",
        help=(
            "Generate policy_report.md — a formatted report of all indexed documents "
            "with source, doc number, title, date released, and download link. "
            "Combine with --dry-run to produce the report without downloading anything."
        ))
    parser.add_argument("--report-file", default="policy_report.md",
        help="Filename for the policy report (default: policy_report.md)")
    parser.add_argument("--brave-key", default=os.environ.get("BRAVE_API_KEY", ""),
        help="Brave Search API key for URL discovery fallback")
    parser.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN", ""),
        help="GitHub personal access token")
    parser.add_argument("--github-repo", default=os.environ.get("GITHUB_REPO", ""),
        help="GitHub repo as owner/repo-name")
    args = parser.parse_args()

    output_dir = Path(args.output).resolve()
    setup_logging(output_dir)
    log.info(
        "Navy Policy Downloader v2 | output=%s | dry_run=%s | report=%s",
        output_dir, args.dry_run, args.report,
    )

    all_nums = [f"{i:02d}" for i in range(1, 16)]
    if args.sources.lower() == "all":
        selected = all_nums
    else:
        selected = [s.strip().zfill(2) for s in args.sources.split(",")]

    session = make_session()
    scrapers = build_scrapers(session, output_dir, args.brave_key, args.dry_run, selected)

    all_docs: list[PolicyDocument] = []
    for scraper in scrapers:
        try:
            docs = scraper.scrape()
            all_docs.extend(docs)
        except Exception as exc:
            log.error("Scraper %s failed: %s", scraper.source_code, exc, exc_info=True)

    # Always write the standard index outputs
    write_json_index(all_docs, output_dir)
    write_md_index(all_docs, output_dir)
    write_review_file(all_docs, output_dir)

    # Write the policy report when --report is passed (or always if --dry-run)
    if args.report or args.dry_run:
        write_policy_report(all_docs, output_dir, selected, args.report_file)

    dl = sum(1 for d in all_docs if d.downloaded)
    log.info(
        "Complete. Total=%d | Downloaded=%d | Review=%d",
        len(all_docs), dl, len(all_docs) - dl,
    )

    # GitHub push
    if args.github_token and args.github_repo:
        push_to_github(output_dir, args.github_token, args.github_repo)


if __name__ == "__main__":
    main()
