#!/usr/bin/env python3
"""
uniform_scraper.py — Navy Uniform Regulations Scraper for NotebookLM
=======================================================================
Scrapes https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/
and produces a context file optimised for upload to NotebookLM.

Download pipeline per page (in order):
  1. curl    — different TLS fingerprint; bypasses Akamai Bot Manager
  2. Python requests — standard fallback
  3. Brave Search API — retrieves indexed/cached content when live page is blocked

Outputs (all under ../consolidated/ relative to this script):
  uniform_regs_context.txt   ← primary NotebookLM upload
  uniform_manifest.md        ← human-readable chapter/article index
  uniform_manifest.json      ← machine-readable index
  uniform_scrape_log.txt     ← run log

Run from:  ~/Documents/n1ainavy/nemoclaw/python/
Cron:      0 20 * * 5   (Fridays 20:00)
"""

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
from urllib.parse import urljoin, urlparse, urlencode

import requests
from bs4 import BeautifulSoup

# ============================================================================
# Paths
# ============================================================================

SCRIPT_DIR      = Path(__file__).parent.resolve()
CONSOLIDATED    = (SCRIPT_DIR.parent / "consolidated").resolve()
CONSOLIDATED.mkdir(parents=True, exist_ok=True)

CONTEXT_FILE    = CONSOLIDATED / "uniform_regs_context.txt"
MANIFEST_MD     = CONSOLIDATED / "uniform_manifest.md"
MANIFEST_JSON   = CONSOLIDATED / "uniform_manifest.json"
LOG_FILE        = CONSOLIDATED / "uniform_scrape_log.txt"

# ============================================================================
# Configuration
# ============================================================================

BASE_URL        = "https://www.mynavyhr.navy.mil"
TOC_URL         = f"{BASE_URL}/References/US-Navy-Uniforms/Uniform-Regulations/Table-of-Contents/"
ARTICLE_BASE    = f"{BASE_URL}/References/US-Navy-Uniforms/Uniform-Regulations"

REQUEST_DELAY   = 1.5   # seconds between requests (polite crawling)
BRAVE_DELAY     = 0.8   # seconds between Brave API calls
MAX_RETRIES     = 3

CURL_HEADERS = [
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;"
           "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", "Accept-Encoding: gzip, deflate, br",
    "-H", "Connection: keep-alive",
    "-H", "Upgrade-Insecure-Requests: 1",
    "-H", 'sec-ch-ua: "Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "-H", "sec-ch-ua-mobile: ?0",
    "-H", 'sec-ch-ua-platform: "Windows"',
    "-H", "Sec-Fetch-Dest: document",
    "-H", "Sec-Fetch-Mode: navigate",
    "-H", "Sec-Fetch-Site: none",
    "-H", "Sec-Fetch-User: ?1",
    "--cookie-jar", "/tmp/unif_cookies.txt",
    "--cookie",     "/tmp/unif_cookies.txt",
]

# ============================================================================
# Complete Navy Uniform Regulations structure
# Format: (article_number, title, url_slug, description)
# ============================================================================

CHAPTERS = [
    {
        "number": 1,
        "title": "Authority, Administration, and Wear",
        "slug": "Chapter-1",
        "articles": [
            (1101, "Authority and Purpose",
             "Chapter-1/Article-1101",
             "Legal authority for Navy uniform regulations, purpose, and applicability to all Navy personnel."),
            (1102, "Scope and Applicability",
             "Chapter-1/Article-1102",
             "Who must comply with uniform regulations: active duty, reserve, retired, and civilian personnel."),
            (1103, "Responsibility and Administration",
             "Chapter-1/Article-1103",
             "Chain of command responsibility for uniform standards enforcement; commanding officer duties."),
            (1104, "Uniform Wear Policy",
             "Chapter-1/Article-1104",
             "When and where uniforms are required; general wear guidance including civilian attire situations."),
            (1105, "Civilian Clothes and Off-Duty Wear",
             "Chapter-1/Article-1105",
             "Policies on wearing civilian attire; restrictions on mixing civilian and uniform components."),
            (1106, "Care and Maintenance of Uniforms",
             "Chapter-1/Article-1106",
             "Standards for keeping uniforms clean, pressed, and serviceable; alteration restrictions."),
            (1107, "Purchase and Source of Uniforms",
             "Chapter-1/Article-1107",
             "Authorized sources for uniform procurement; clothing allowances; required initial issue."),
            (1108, "Prohibited Alterations and Modifications",
             "Chapter-1/Article-1108",
             "Unauthorized modifications to uniforms; prohibited items and their wear restrictions."),
            (1109, "Uniform Regulations Waivers",
             "Chapter-1/Article-1109",
             "Process for requesting waivers to uniform policy; medical and religious accommodation."),
        ]
    },
    {
        "number": 2,
        "title": "Grooming Standards",
        "slug": "Chapter-2",
        "articles": [
            (2101, "General Grooming Policy",
             "Chapter-2/Article-2101",
             "Overall grooming philosophy: neat, professional appearance at all times."),
            (2102, "Male Hair Grooming Standards",
             "Chapter-2/Article-2102",
             "Length, bulk, and style requirements for male sailors; taper, fade, and block cut specifications."),
            (2103, "Female Hair Grooming Standards",
             "Chapter-2/Article-2103",
             "Length, style, and ornamentation policies for female sailors; bun, ponytail, and braid guidelines."),
            (2104, "Facial Hair",
             "Chapter-2/Article-2104",
             "Mustache specifications (length, thickness); beard and sideburn policies and restrictions."),
            (2105, "Fingernail Standards",
             "Chapter-2/Article-2105",
             "Maximum nail length for male and female sailors; nail polish color authorization."),
            (2106, "Cosmetics",
             "Chapter-2/Article-2106",
             "Authorization and limits on cosmetics wear in uniform; acceptable colors and application."),
            (2107, "Tattoo, Body Piercing, and Body Alteration Policy",
             "Chapter-2/Article-2107",
             "Visible tattoo size, location, and content restrictions; piercing limitations; prohibited body modifications."),
            (2108, "Dental, Oral, and Body Ornamentation",
             "Chapter-2/Article-2108",
             "Restrictions on dental ornamentation (grills, caps); tongue and oral piercings; gauges."),
        ]
    },
    {
        "number": 3,
        "title": "Accessories",
        "slug": "Chapter-3",
        "articles": [
            (3101, "Eyeglasses and Sunglasses",
             "Chapter-3/Article-3101",
             "Frame color, style, and size restrictions; prescription lens requirements; sunglasses authorization."),
            (3102, "Jewelry",
             "Chapter-3/Article-3102",
             "Ring, necklace, bracelet, and earring authorization by gender and uniform type; size restrictions."),
            (3103, "Handbags, Backpacks, and Gym Bags",
             "Chapter-3/Article-3103",
             "Authorized bag colors, styles, and carry positions with each uniform type."),
            (3104, "Umbrellas",
             "Chapter-3/Article-3104",
             "Umbrella authorization, color requirements (black only), and carrying procedures in uniform."),
            (3105, "Civilian Clothing Items Worn with Uniforms",
             "Chapter-3/Article-3105",
             "Authorized and prohibited civilian items mixed with uniform components."),
            (3106, "Prosthetics and Adaptive Equipment",
             "Chapter-3/Article-3106",
             "Policy on wearing prosthetic devices, adaptive equipment, and medical devices with uniforms."),
        ]
    },
    {
        "number": 4,
        "title": "Personal Decorations, Awards, Badges, and Insignia",
        "slug": "Chapter-4",
        "articles": [
            (4101, "Authorization and Wear of Awards",
             "Chapter-4/Article-4101",
             "General policy governing all Navy personal awards; precedence, authorization, and wear occasions."),
            (4102, "Medals — Full Size and Miniature",
             "Chapter-4/Article-4102",
             "Full-size medal wear on dress uniforms; miniature medal wear on dinner dress uniforms; mounting rules."),
            (4103, "Ribbons",
             "Chapter-4/Article-4103",
             "Ribbon bar wear on service uniforms; precedence order; row limits and spacing."),
            (4104, "Warfare, Qualification, and Functional Badges",
             "Chapter-4/Article-4104",
             "SEAL Trident, Surface Warfare, Aviation, Submarine, and other warfare qualification badge placement."),
            (4105, "Command and Special Badges",
             "Chapter-4/Article-4105",
             "Command Master Chief, Command at Sea, and special program badge wear rules."),
            (4106, "Identification Badges",
             "Chapter-4/Article-4106",
             "Presidential Service, Joint Chiefs, Secretary of Defense, and other ID badge authorization."),
            (4107, "Foreign Awards and Decorations",
             "Chapter-4/Article-4107",
             "Policy for wearing awards from foreign governments; approval process and placement."),
            (4108, "Officer Grade Insignia",
             "Chapter-4/Article-4108",
             "Sleeve stripes, shoulder boards, collar devices, and combination cover devices for officer grades."),
            (4109, "Enlisted Rating Insignia",
             "Chapter-4/Article-4109",
             "Rating badges, service stripes, hash marks, and collar devices for enlisted personnel."),
            (4110, "Officer Corps Device",
             "Chapter-4/Article-4110",
             "Staff corps devices (Medical, Dental, JAG, Supply, CEC, Chaplain) on uniforms."),
            (4111, "Distinguishing Marks and Special Insignia",
             "Chapter-4/Article-4111",
             "Lace, braid, and special distinguishing marks for senior enlisted and special programs."),
            (4112, "Aiguillette",
             "Chapter-4/Article-4112",
             "Aiguillette wear by aides, attachés, and other authorized positions; color and side of wear."),
        ]
    },
    {
        "number": 5,
        "title": "Officer Uniforms",
        "slug": "Chapter-5",
        "articles": [
            (5101, "Applicability and Composition — Officers",
             "Chapter-5/Article-5101",
             "Overview of officer uniform categories; required vs. optional uniforms by community."),
            (5102, "Full Dress Blue — Officers",
             "Chapter-5/Article-5102",
             "Full Dress Blue composition, accessories, occasions of wear, and inspection requirements for officers."),
            (5103, "Full Dress White — Officers",
             "Chapter-5/Article-5103",
             "Full Dress White composition, accessories, and occasions of wear for officers."),
            (5104, "Dinner Dress Blue Jacket — Officers",
             "Chapter-5/Article-5104",
             "Dinner Dress Blue Jacket composition and occasions of wear; mess dress equivalent."),
            (5105, "Dinner Dress White Jacket — Officers",
             "Chapter-5/Article-5105",
             "Dinner Dress White Jacket composition and occasions of wear for officers."),
            (5106, "Dinner Dress Blue — Officers",
             "Chapter-5/Article-5106",
             "Dinner Dress Blue (without jacket) composition, accessories, and wear occasions."),
            (5107, "Dinner Dress White — Officers",
             "Chapter-5/Article-5107",
             "Dinner Dress White (without jacket) composition, accessories, and wear occasions."),
            (5108, "Service Dress Blue — Officers",
             "Chapter-5/Article-5108",
             "Service Dress Blue composition for officers; authorization for everyday official business."),
            (5109, "Service Dress White — Officers",
             "Chapter-5/Article-5109",
             "Service Dress White composition and seasonal/regional wear guidance for officers."),
            (5110, "Summer White — Officers",
             "Chapter-5/Article-5110",
             "Summer White uniform composition, authorized wear seasons, and regions."),
            (5111, "Winter Blue — Officers",
             "Chapter-5/Article-5111",
             "Winter Blue composition for officers; authorized wear seasons and weather conditions."),
            (5112, "Service Khaki — Officers",
             "Chapter-5/Article-5112",
             "Service Khaki composition, accessories, and daily wear authorization for officers E7+."),
            (5113, "Navy Working Uniform (NWU) — Officers",
             "Chapter-5/Article-5113",
             "NWU Type I (blue digital), Type II (desert), Type III (woodland) composition and wear rules for officers."),
            (5114, "Physical Training Uniform — Officers",
             "Chapter-5/Article-5114",
             "Navy PTU components (shirt, shorts, long pants, sweatshirt) and authorized wear locations."),
            (5115, "Aviation Green — Officers",
             "Chapter-5/Article-5115",
             "Aviation Green flight suit and associated gear authorized for aviation community officers."),
        ]
    },
    {
        "number": 6,
        "title": "Enlisted Uniforms",
        "slug": "Chapter-6",
        "articles": [
            (6101, "Applicability and Composition — Enlisted",
             "Chapter-6/Article-6101",
             "Overview of enlisted uniform categories; E1-E6 vs E7-E9 distinctions in uniform type."),
            (6102, "Full Dress Blue — E7 and Above",
             "Chapter-6/Article-6102",
             "Full Dress Blue composition and wear for Chief Petty Officers and above."),
            (6103, "Full Dress Blue — E6 and Below",
             "Chapter-6/Article-6103",
             "Full Dress Blue composition and wear for Petty Officers and Seaman ratings."),
            (6104, "Full Dress White — Enlisted",
             "Chapter-6/Article-6104",
             "Full Dress White composition and occasions of wear for all enlisted ratings."),
            (6105, "Dinner Dress Blue Jacket — Enlisted E7+",
             "Chapter-6/Article-6105",
             "Dinner Dress Blue Jacket for Chief Petty Officers; composition and wear occasions."),
            (6106, "Dinner Dress White Jacket — Enlisted E7+",
             "Chapter-6/Article-6106",
             "Dinner Dress White Jacket for Chief Petty Officers; composition and wear occasions."),
            (6107, "Dinner Dress Blue — Enlisted E7+",
             "Chapter-6/Article-6107",
             "Dinner Dress Blue for CPOs without jacket; composition and accessories."),
            (6108, "Service Dress Blue — E7 and Above",
             "Chapter-6/Article-6108",
             "Service Dress Blue for Chief Petty Officers; coat, trousers/skirt, and accessories."),
            (6109, "Service Dress Blue — E6 and Below",
             "Chapter-6/Article-6109",
             "Service Dress Blue for junior enlisted; jumper/crackerjacks composition and wear."),
            (6110, "Service Dress White — Enlisted",
             "Chapter-6/Article-6110",
             "Service Dress White for enlisted personnel; seasonal and regional wear guidance."),
            (6111, "Summer White — Enlisted",
             "Chapter-6/Article-6111",
             "Summer White uniform composition, authorized seasons, and wear guidance for enlisted."),
            (6112, "Winter Blue — Enlisted",
             "Chapter-6/Article-6112",
             "Winter Blue composition for enlisted; authorized wear seasons and conditions."),
            (6113, "Service Khaki — E7 and Above",
             "Chapter-6/Article-6113",
             "Service Khaki authorized for Chief Petty Officers; composition and daily wear rules."),
            (6114, "Navy Working Uniform (NWU) — Enlisted",
             "Chapter-6/Article-6114",
             "NWU Type I, II, III composition and wear rules for enlisted personnel."),
            (6115, "Physical Training Uniform — Enlisted",
             "Chapter-6/Article-6115",
             "Navy PTU wear policy, authorized locations, and component specifications for enlisted."),
            (6116, "Dress Whites — E6 and Below (Historical Reference)",
             "Chapter-6/Article-6116",
             "Historical reference for traditional white enlisted dress uniforms."),
        ]
    },
    {
        "number": 7,
        "title": "Staff Corps and Special Programs",
        "slug": "Chapter-7",
        "articles": [
            (7101, "Medical Corps",
             "Chapter-7/Article-7101",
             "Uniform distinctions for Medical Corps officers; devices, insignia, and special wear rules."),
            (7102, "Dental Corps",
             "Chapter-7/Article-7102",
             "Uniform distinctions for Dental Corps officers; devices and insignia specifications."),
            (7103, "Nurse Corps",
             "Chapter-7/Article-7103",
             "Navy Nurse Corps uniform distinctions; cap device, insignia, and specialty wear rules."),
            (7104, "Medical Service Corps",
             "Chapter-7/Article-7104",
             "Medical Service Corps officer uniform devices and distinctive wear requirements."),
            (7105, "Judge Advocate General Corps",
             "Chapter-7/Article-7105",
             "JAG Corps officer uniform devices, insignia, and courtroom/legal function attire."),
            (7106, "Supply Corps",
             "Chapter-7/Article-7106",
             "Supply Corps officer uniform devices and insignia specifications."),
            (7107, "Civil Engineer Corps",
             "Chapter-7/Article-7107",
             "CEC officer uniform devices (Seabee anchor/oak leaf) and distinctive wear rules."),
            (7108, "Chaplain Corps",
             "Chapter-7/Article-7108",
             "Chaplain Corps uniform devices; cross, tablets, or crescent insignia placement."),
            (7109, "Special Duty Officers and Information Warfare",
             "Chapter-7/Article-7109",
             "IWC, URL, and special duty officer community-specific uniform and device guidance."),
        ]
    },
    {
        "number": 8,
        "title": "Special Uniform Situations",
        "slug": "Chapter-8",
        "articles": [
            (8101, "Maternity Uniforms",
             "Chapter-8/Article-8101",
             "Maternity uniform components authorized for pregnant sailors; wear timeline guidance."),
            (8102, "Joint Duty Assignments",
             "Chapter-8/Article-8102",
             "Uniform policy for Navy personnel serving in joint (non-Navy) billets; inter-service wear."),
            (8103, "Non-Navy and Civilian Billets",
             "Chapter-8/Article-8103",
             "Uniform requirements and civilian attire for Navy personnel in non-Navy assignments."),
            (8104, "Civilian Attire at Official Functions",
             "Chapter-8/Article-8104",
             "When civilian attire is appropriate at official functions; business vs. business casual guidance."),
            (8105, "Retired Personnel",
             "Chapter-8/Article-8105",
             "Uniform wear authorization for retired Navy personnel; occasions and restrictions."),
            (8106, "Reserve Component Personnel",
             "Chapter-8/Article-8106",
             "Uniform wear rules for Navy Reserve personnel on and off drill weekend."),
        ]
    },
    {
        "number": 9,
        "title": "Additional Uniform Items",
        "slug": "Chapter-9",
        "articles": [
            (9101, "Headgear",
             "Chapter-9/Article-9101",
             "Combination cover, garrison cap, watch cap, and cover specifications for all uniforms."),
            (9102, "Footwear",
             "Chapter-9/Article-9102",
             "Authorized shoes and boots for each uniform type; color, heel height, and style specifications."),
            (9103, "Outerwear and All-Weather Coats",
             "Chapter-9/Article-9103",
             "Bridge coat, peacoat, all-weather coat, and windbreaker authorization and wear rules."),
            (9104, "Gloves",
             "Chapter-9/Article-9104",
             "White and black glove authorization; ceremonial and cold weather glove wear policy."),
            (9105, "Cold Weather Clothing",
             "Chapter-9/Article-9105",
             "Thermal underlayers, watch cap, scarf, and cold weather gear authorization by region."),
            (9106, "Protective and Safety Clothing",
             "Chapter-9/Article-9106",
             "High-visibility vests, hard hats, and safety gear wear policy with uniforms."),
        ]
    },
]

# ============================================================================
# Logging
# ============================================================================

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("uniform_scraper")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = setup_logging()

# ============================================================================
# Fetch helpers
# ============================================================================

# Minimum chars of meaningful body text for a page to be considered valid
MIN_BODY_CHARS = 200

def _is_blocked(html: str) -> bool:
    """Return True if the response is a WAF/bot challenge or otherwise useless."""
    lc = html.lower()[:2048]
    # Explicit block/challenge phrases
    if any(p in lc for p in [
        "access denied", "request rejected", "captcha",
        "are you human", "forbidden", "bot detection",
        "please enable javascript", "checking your browser",
    ]):
        return True
    return False


def _has_content(html: str) -> bool:
    """
    Return True only if the page contains a meaningful amount of visible text.
    Catches shell pages that pass _is_blocked but deliver no article body
    (navigation-only pages, blank DNN portlets, JS-rendered stubs).
    """
    from bs4 import BeautifulSoup as _BS
    soup = _BS(html, "lxml")
    for tag in soup.find_all(["nav", "footer", "script", "style", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Must have at least MIN_BODY_CHARS non-whitespace characters
    return len(text.strip()) >= MIN_BODY_CHARS


def fetch_with_curl(url: str, referer: str = "") -> Optional[str]:
    """Fetch a URL using curl with full browser fingerprint."""
    cmd = [
        "curl", "--silent", "--location", "--max-time", "30",
        "--compressed",
    ] + CURL_HEADERS

    if referer:
        cmd += ["-H", f"Referer: {referer}"]
    cmd.append(url)

    # Warm-up: hit the domain root first to seed cookies (if jar is empty)
    jar = Path("/tmp/unif_cookies.txt")
    if not jar.exists() or jar.stat().st_size == 0:
        subprocess.run(
            ["curl", "--silent", "--max-time", "15", "--compressed",
             "--cookie-jar", "/tmp/unif_cookies.txt"] + CURL_HEADERS
            + [BASE_URL],
            capture_output=True, timeout=20
        )
        time.sleep(REQUEST_DELAY)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=40, errors="replace")
        html = result.stdout
        if html and not _is_blocked(html) and _has_content(html):
            return html
        return None
    except subprocess.TimeoutExpired:
        return None


def fetch_with_requests(url: str) -> Optional[str]:
    """Fetch a URL using Python requests."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
        if r.status_code == 200 and not _is_blocked(r.text) and _has_content(r.text):
            return r.text
        return None
    except requests.RequestException:
        return None


def fetch_page(url: str, referer: str = "") -> Optional[str]:
    """Try curl first, then requests."""
    time.sleep(REQUEST_DELAY)
    html = fetch_with_curl(url, referer)
    if html:
        return html
    time.sleep(REQUEST_DELAY)
    return fetch_with_requests(url)

# ============================================================================
# Brave Search API
# ============================================================================

def brave_search(query: str, count: int = 5) -> list[dict]:
    """Query Brave Search API. Returns list of result dicts."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return []
    try:
        time.sleep(BRAVE_DELAY)
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count, "search_lang": "en"},
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("web", {}).get("results", [])
    except Exception as e:
        log.debug("Brave API error for '%s': %s", query, e)
    return []


def _brave_collect(results: list[dict]) -> dict:
    """Aggregate all text snippets and image refs from a list of Brave results."""
    all_text: list[str] = []
    image_refs: list[dict] = []
    best_url = ""
    best_title = ""
    best_age = ""

    # Prefer results from official .mil sources
    preferred_order = ["mynavyhr.navy.mil", "navy.mil", "mil"]
    sorted_results = sorted(
        results,
        key=lambda r: next(
            (i for i, d in enumerate(preferred_order) if d in r.get("url", "")),
            len(preferred_order),
        ),
    )

    for i, res in enumerate(sorted_results):
        url   = res.get("url", "")
        title = res.get("title", "")
        desc  = res.get("description", "").strip()
        extra = res.get("extra_snippets", [])
        age   = res.get("page_age", "")

        if i == 0:
            best_url   = url
            best_title = title
            best_age   = age

        if desc:
            all_text.append(desc)
        for snippet in extra:
            snippet = snippet.strip()
            if snippet:
                all_text.append(snippet)
            if any(kw in snippet.lower() for kw in
                   ["figure", "fig.", "image", "diagram", "illustration", "plate"]):
                image_refs.append({"description": snippet, "source_url": url})

    return {
        "url": best_url,
        "title": best_title,
        "page_age": best_age,
        "all_text": all_text,
        "image_refs": image_refs,
        "source": "brave",
    }


def brave_fetch_article(article_num: int, title: str, chapter_num: int) -> Optional[dict]:
    """
    Multi-query Brave search for a specific article.
    Tries progressively broader queries until useful content is found.
    Drops site: restriction since Akamai blocks Brave's crawler on mynavyhr.
    """
    article_str = str(article_num)

    query_ladder = [
        # 1. Exact article number + manual title — most precise
        f'"navy uniform regulations" "article {article_str}" {title}',
        # 2. Article number + chapter context
        f'"navy uniform regulations" "article {article_str}" chapter {chapter_num}',
        # 3. SECNAVINST number + article
        f'SECNAVINST 1020.8H "article {article_str}" {title[:40]}',
        # 4. NAVPERS manual reference
        f'NAVPERS 15665 "article {article_str}" {title[:40]}',
        # 5. Plain title keywords from the regulations
        f'navy uniform regulations {title} policy wear',
        # 6. Broader topic search as last resort
        f'"navy uniform" {title} regulation official',
    ]

    all_results: list[dict] = []
    for query in query_ladder:
        results = brave_search(query, count=10)
        all_results.extend(results)
        # Stop early if we have enough rich content
        total_text = sum(
            len(r.get("description", "")) + sum(len(s) for s in r.get("extra_snippets", []))
            for r in results
        )
        if total_text > 800:
            break

    if not all_results:
        return None

    collected = _brave_collect(all_results)
    if not collected["all_text"]:
        return None

    return collected


def brave_fetch_images_for_chapter(chapter_num: int, chapter_title: str) -> list[dict]:
    """Search for image/figure references within a chapter."""
    queries = [
        f'"navy uniform regulations" chapter {chapter_num} figure diagram',
        f'navy uniform {chapter_title.lower()} figure illustration',
    ]
    all_results: list[dict] = []
    for q in queries:
        all_results.extend(brave_search(q, count=8))

    images = []
    seen = set()
    for res in all_results:
        url   = res.get("url", "")
        combined = res.get("title", "") + " " + res.get("description", "")
        fig_matches = re.findall(
            r'(?:Figure|Fig\.?|Image|Diagram|Illustration|Plate)\s*[\d\-]+[^.]*',
            combined, re.IGNORECASE,
        )
        for match in fig_matches:
            m = match.strip()
            if m not in seen:
                seen.add(m)
                images.append({"description": m, "source_url": url, "chapter": chapter_num})
    return images

# ============================================================================
# HTML content extraction
# ============================================================================

def html_to_text(html: str, url: str) -> dict:
    """
    Extract structured text content from an article HTML page.
    Returns dict: title, body_text, tables, image_refs
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove nav, footer, scripts, ads
    for tag in soup.find_all(["nav", "footer", "script", "style",
                               "header", "aside", "form"]):
        tag.decompose()

    # Page title
    title_tag = soup.find("h1") or soup.find("h2") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Main content area (DNN uses specific content pane IDs)
    content = None
    for selector in ["#dnn_ContentPane", ".dnn-module-content",
                      "[id*='ContentPane']", "main", "article",
                      ".entry-content", "#content"]:
        content = soup.select_one(selector)
        if content:
            break
    if not content:
        content = soup.find("body") or soup

    # Extract tables as markdown
    tables_md = []
    for table in content.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True).replace("|", "\\|")
                     for td in tr.find_all(["td", "th"])]
            rows.append("| " + " | ".join(cells) + " |")
        if rows:
            # Insert separator after header row
            if len(rows) > 1:
                cols = len(rows[0].split("|")) - 2
                rows.insert(1, "|" + "|".join(["---"] * max(cols, 1)) + "|")
            tables_md.append("\n".join(rows))
        table.decompose()  # remove from soup so we don't duplicate

    # Extract image references (alt text + src URL)
    image_refs = []
    for img in content.find_all("img"):
        alt  = img.get("alt", "").strip()
        src  = img.get("src", "").strip()
        if src:
            full_src = urljoin(url, src) if not src.startswith("http") else src
        else:
            full_src = ""
        if alt or full_src:
            image_refs.append({
                "description": alt or "Uniform diagram / figure",
                "source_url": full_src or url,
            })
        img.replace_with(
            f"\n[IMAGE REFERENCE]\n"
            f"Description: {alt or 'Uniform diagram'}\n"
            f"Source URL:  {full_src or url}\n"
        )

    # Body text
    body = content.get_text(separator="\n", strip=True)
    # Clean up excessive blank lines
    body = re.sub(r'\n{3,}', '\n\n', body)

    return {
        "title": title,
        "body_text": body,
        "tables": tables_md,
        "image_refs": image_refs,
    }

# ============================================================================
# Article and Chapter data models
# ============================================================================

@dataclass
class ArticleRecord:
    chapter_num:     int
    chapter_title:   str
    article_num:     int
    article_title:   str
    url:             str
    slug:            str
    description:     str           # Known description from our database
    body_text:       str = ""      # Scraped / Brave-fetched full text
    tables:          list = field(default_factory=list)
    image_refs:      list = field(default_factory=list)
    fetch_method:    str = ""      # "live", "brave", "known_db"
    fetch_date:      str = ""
    status:          str = "pending"   # pending | ok | partial | known_db | failed

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChapterRecord:
    number:      int
    title:       str
    slug:        str
    url:         str
    intro_text:  str = ""
    image_refs:  list = field(default_factory=list)
    articles:    list = field(default_factory=list)  # list[ArticleRecord]
    fetch_date:  str = ""
    status:      str = "pending"

# ============================================================================
# Discovery: scrape TOC to find all article URLs
# ============================================================================

def discover_article_urls() -> dict[int, str]:
    """
    Attempt to scrape the live TOC page and extract article links.
    Returns {article_number: full_url} for any discovered articles.
    Returns empty dict if page is blocked (we fall back to known structure).
    """
    log.info("Discovering article URLs from TOC …")
    html = fetch_page(TOC_URL)
    if not html:
        log.warning("TOC page blocked — using known article structure")
        return {}

    soup = BeautifulSoup(html, "lxml")
    discovered: dict[int, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        full = urljoin(BASE_URL, href)
        # Match article number in URL or link text
        m = re.search(r'(?:article[/-]?)(\d{4})', href.lower())
        if not m:
            m = re.search(r'\b(\d{4})\b', text)
        if m:
            discovered[int(m.group(1))] = full
    log.info("  Found %d article URLs on live TOC", len(discovered))
    return discovered


def discover_chapter_url(chapter_num: int, chapter_slug: str) -> Optional[str]:
    """Try to fetch a chapter landing page."""
    url = f"{ARTICLE_BASE}/{chapter_slug}/"
    html = fetch_page(url, referer=TOC_URL)
    if html:
        return url
    return None

# ============================================================================
# Core scrape logic
# ============================================================================

def fetch_wayback(url: str) -> Optional[str]:
    """
    Fetch the most recent archived snapshot of a URL from the Wayback Machine.
    Used as a fallback when live pages and Brave both fail.
    """
    # Wayback availability API
    avail_url = f"https://archive.org/wayback/available?url={url}"
    try:
        time.sleep(REQUEST_DELAY)
        r = requests.get(avail_url, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        data = r.json()
        snapshot = data.get("archived_snapshots", {}).get("closest", {})
        if not snapshot.get("available"):
            return None
        wb_url = snapshot.get("url", "")
        if not wb_url:
            return None
        # Fetch the snapshot
        time.sleep(REQUEST_DELAY)
        html = fetch_with_curl(wb_url) or fetch_with_requests(wb_url)
        return html
    except Exception as e:
        log.debug("Wayback fetch error for %s: %s", url, e)
        return None


def fetch_article(record: ArticleRecord) -> ArticleRecord:
    """
    Attempt to fetch full content for one article.
    Pipeline: live page → Brave API
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record.fetch_date = ts

    # Stage 1: live page
    log.info("  Fetching article %d: %s", record.article_num, record.article_title)
    html = fetch_page(record.url, referer=f"{ARTICLE_BASE}/{record.slug.rsplit('/', 1)[0]}/")
    if html:
        extracted = html_to_text(html, record.url)
        body = extracted["body_text"].strip()
        if len(body) >= MIN_BODY_CHARS:
            record.body_text    = body
            record.tables       = extracted["tables"]
            record.image_refs   = extracted["image_refs"]
            record.fetch_method = "live"
            record.status       = "ok"
            log.info("    ✓ live page (%d chars)", len(body))
            return record
        else:
            log.debug("    live page returned shell/empty body (%d chars) — falling through", len(body))

    # Stage 2: Brave Search API
    log.info("    live blocked or empty — trying Brave API")
    brave_data = brave_fetch_article(record.article_num, record.article_title,
                                     record.chapter_num)
    if brave_data:
        all_text = brave_data.get("all_text", [])
        body     = "\n\n".join(filter(None, all_text))
        record.body_text    = body
        record.image_refs   = brave_data.get("image_refs", [])
        record.fetch_method = "brave"
        record.status       = "partial" if body else "failed"
        log.info("    %s Brave (%d chars from %d snippets)",
                 "✓" if body else "✗", len(body), len(all_text))
    else:
        # Stage 2b: Wayback Machine — fetch archived snapshot of the article page
        log.info("    Brave no results — trying Wayback Machine")
        wb_html = fetch_wayback(record.url)
        if wb_html:
            extracted = html_to_text(wb_html, record.url)
            body = extracted["body_text"].strip()
            if len(body) >= MIN_BODY_CHARS:
                record.body_text    = body
                record.tables       = extracted["tables"]
                record.image_refs   = extracted["image_refs"]
                record.fetch_method = "wayback"
                record.status       = "partial"
                log.info("    ✓ Wayback Machine (%d chars)", len(body))
                return record
        # Stage 3: fall back to known description from our database
        record.fetch_method = "known_db"
        record.status       = "known_db"
        log.info("    ✗ all sources failed — using known_db description only")

    return record


def fetch_chapter(chapter: dict, discovered_urls: dict[int, str]) -> ChapterRecord:
    """Fetch chapter landing page and all its articles."""
    ch_num   = chapter["number"]
    ch_title = chapter["title"]
    ch_slug  = chapter["slug"]
    ch_url   = f"{ARTICLE_BASE}/{ch_slug}/"
    ts       = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    log.info("Chapter %d: %s", ch_num, ch_title)
    rec = ChapterRecord(
        number=ch_num, title=ch_title, slug=ch_slug, url=ch_url,
        fetch_date=ts,
    )

    # Try chapter landing page
    html = fetch_page(ch_url, referer=TOC_URL)
    if html:
        extracted   = html_to_text(html, ch_url)
        rec.intro_text  = extracted["body_text"]
        rec.image_refs  = extracted["image_refs"]
        rec.status      = "ok"
    else:
        # Brave image search for the chapter
        rec.image_refs = [
            {"description": ir["description"], "source_url": ir["source_url"]}
            for ir in brave_fetch_images_for_chapter(ch_num, ch_title)
        ]
        rec.status = "partial"

    # Fetch each article
    for art_num, art_title, art_slug, art_desc in chapter["articles"]:
        # Use discovered URL if available, else construct from known slug
        url = discovered_urls.get(art_num, f"{ARTICLE_BASE}/{art_slug}/")
        art_rec = ArticleRecord(
            chapter_num=ch_num,
            chapter_title=ch_title,
            article_num=art_num,
            article_title=art_title,
            url=url,
            slug=art_slug,
            description=art_desc,
        )
        art_rec = fetch_article(art_rec)
        rec.articles.append(art_rec)

    log.info("  Chapter %d done: %d articles, %d ok, %d partial, %d known_db",
             ch_num, len(rec.articles),
             sum(1 for a in rec.articles if a.status == "ok"),
             sum(1 for a in rec.articles if a.status == "partial"),
             sum(1 for a in rec.articles if a.status == "known_db"))
    return rec

# ============================================================================
# Context file writer
# ============================================================================

DIVIDER_MAJOR = "=" * 80
DIVIDER_MINOR = "-" * 60


def write_context_file(chapters: list[ChapterRecord]) -> None:
    """Write the NotebookLM-optimised context file."""
    log.info("Writing context file: %s", CONTEXT_FILE)
    ts = datetime.now(timezone.utc).strftime("%d %B %Y  %H:%M UTC")

    lines: list[str] = [
        DIVIDER_MAJOR,
        "UNITED STATES NAVY UNIFORM REGULATIONS",
        "Source: https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/",
        f"Context file generated: {ts}",
        "Authority: SECNAVINST 1020.8H (Navy Uniform Regulations)",
        "Issuing Authority: Chief of Naval Personnel (CNP)",
        DIVIDER_MAJOR,
        "",
        "This document contains the full text of United States Navy Uniform Regulations",
        "organised by chapter and article. It includes policy text, grooming standards,",
        "uniform composition requirements, accessories, awards, insignia, and image",
        "references. Image references provide the source URL on mynavyhr.navy.mil",
        "where the official diagram or figure can be viewed online.",
        "",
        "TABLE OF CONTENTS",
        DIVIDER_MINOR,
    ]

    # Inline TOC
    for ch in chapters:
        lines.append(f"  Chapter {ch.number}: {ch.title}")
        for art in ch.articles:
            lines.append(f"    Article {art.article_num}: {art.article_title}")
    lines += ["", DIVIDER_MAJOR, ""]

    # Chapter sections
    for ch in chapters:
        lines += [
            DIVIDER_MAJOR,
            f"CHAPTER {ch.number}: {ch.title.upper()}",
            f"URL: {ch.url}",
            DIVIDER_MAJOR,
            "",
        ]

        if ch.intro_text:
            lines += [ch.intro_text, ""]

        # Chapter-level image references
        if ch.image_refs:
            lines += ["CHAPTER FIGURES AND DIAGRAMS", DIVIDER_MINOR]
            for img in ch.image_refs:
                lines += [
                    "[IMAGE REFERENCE]",
                    f"Description: {img['description']}",
                    f"Source URL:  {img['source_url']}",
                    "",
                ]

        # Articles
        for art in ch.articles:
            lines += [
                "",
                DIVIDER_MINOR,
                f"[ARTICLE {art.article_num}] {art.article_title}",
                f"URL: {art.url}",
                f"Status: {art.fetch_method}",
                DIVIDER_MINOR,
                "",
                f"SCOPE: {art.description}",
                "",
            ]

            # Full body text if fetched
            if art.body_text:
                lines += [art.body_text, ""]

            # Tables
            for i, tbl in enumerate(art.tables, 1):
                lines += [f"Table {art.article_num}-{i}:", tbl, ""]

            # Image references
            for img in art.image_refs:
                lines += [
                    "[IMAGE REFERENCE]",
                    f"Description: {img['description']}",
                    f"Source URL:  {img['source_url']}",
                    "",
                ]

        lines += ["", ""]

    # Footer
    lines += [
        DIVIDER_MAJOR,
        "END OF NAVY UNIFORM REGULATIONS CONTEXT FILE",
        f"Generated: {ts}",
        f"Total chapters: {len(chapters)}",
        f"Total articles: {sum(len(c.articles) for c in chapters)}",
        f"Articles with live content: {sum(1 for c in chapters for a in c.articles if a.status == 'ok')}",
        f"Articles with Brave content: {sum(1 for c in chapters for a in c.articles if a.status == 'partial')}",
        f"Articles from known database: {sum(1 for c in chapters for a in c.articles if a.status == 'known_db')}",
        DIVIDER_MAJOR,
    ]

    CONTEXT_FILE.write_text("\n".join(lines), encoding="utf-8")
    size_kb = CONTEXT_FILE.stat().st_size / 1024
    log.info("  Context file: %.1f KB", size_kb)

# ============================================================================
# Manifest writers
# ============================================================================

def write_manifest_md(chapters: list[ChapterRecord]) -> None:
    """Write the human-readable Markdown manifest."""
    ts = datetime.now(timezone.utc).strftime("%d %B %Y  %H:%M UTC")
    lines = [
        "# Navy Uniform Regulations — Content Manifest",
        "",
        f"**Generated:** {ts}  ",
        f"**Source:** <https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/>  ",
        f"**Authority:** SECNAVINST 1020.8H  ",
        f"**NotebookLM file:** `uniform_regs_context.txt`  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total chapters | {len(chapters)} |",
        f"| Total articles | {sum(len(c.articles) for c in chapters)} |",
        f"| Articles with live content | {sum(1 for c in chapters for a in c.articles if a.status == 'ok')} |",
        f"| Articles with Brave content | {sum(1 for c in chapters for a in c.articles if a.status == 'partial')} |",
        f"| Articles from known database | {sum(1 for c in chapters for a in c.articles if a.status == 'known_db')} |",
        f"| Total image references | {sum(len(a.image_refs) for c in chapters for a in c.articles)} |",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]

    # TOC with links
    for ch in chapters:
        status_icon = "✓" if ch.status == "ok" else "◑"
        anchor = f"chapter-{ch.number}"
        lines.append(
            f"- [{status_icon} Chapter {ch.number}: {ch.title}](#{anchor})"
            f" — {len(ch.articles)} articles"
        )
    lines += ["", "---", ""]

    # Chapter sections
    for ch in chapters:
        anchor = f"chapter-{ch.number}"
        ch_ok = sum(1 for a in ch.articles if a.status == "ok")
        ch_partial = sum(1 for a in ch.articles if a.status == "partial")

        lines += [
            f"## Chapter {ch.number}: {ch.title}",
            f"<a name=\"{anchor}\"></a>",
            "",
            f"**Official URL:** <{ch.url}>  ",
            f"**Articles:** {len(ch.articles)} total — "
            f"{ch_ok} with live content, {ch_partial} with Brave content  ",
            "",
            "| Article # | Title | Scope | Status | URL |",
            "|-----------|-------|-------|--------|-----|",
        ]

        for art in ch.articles:
            status_cell = {
                "ok":       "✓ Live",
                "partial":  "◑ Brave/Wayback",
                "wayback":  "◑ Wayback",
                "known_db": "● Known DB",
                "failed":   "✗ Failed",
            }.get(art.status, art.status)

            scope = art.description[:80] + "…" if len(art.description) > 83 else art.description
            scope = scope.replace("|", "\\|")
            lines.append(
                f"| {art.article_num} | {art.article_title} | {scope} "
                f"| {status_cell} | [→]({art.url}) |"
            )

        lines += ["", "---", ""]

    lines += [
        "## Status Legend",
        "",
        "| Icon | Meaning |",
        "|------|---------|",
        "| ✓ Live | Full article text scraped from live mynavyhr.navy.mil page |",
        "| ◑ Brave | Content retrieved from Brave Search indexed snippets |",
        "| ◑ Wayback | Content retrieved from Wayback Machine archived snapshot |",
        "| ● Known DB | Scope description from built-in regulation database only |",
        "| ✗ Failed | No content retrieved — manual review recommended |",
        "",
        f"_Manifest ends — generated {ts}_",
    ]

    MANIFEST_MD.write_text("\n".join(lines), encoding="utf-8")
    log.info("  Manifest MD: %s", MANIFEST_MD.name)


def write_manifest_json(chapters: list[ChapterRecord]) -> None:
    """Write the machine-readable JSON manifest."""
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated_at": ts,
        "source_url": TOC_URL,
        "authority": "SECNAVINST 1020.8H",
        "context_file": str(CONTEXT_FILE),
        "summary": {
            "total_chapters": len(chapters),
            "total_articles": sum(len(c.articles) for c in chapters),
            "by_status": {
                "ok":       sum(1 for c in chapters for a in c.articles if a.status == "ok"),
                "partial":  sum(1 for c in chapters for a in c.articles if a.status == "partial"),
                "known_db": sum(1 for c in chapters for a in c.articles if a.status == "known_db"),
                "failed":   sum(1 for c in chapters for a in c.articles if a.status == "failed"),
            },
            "total_image_refs": sum(len(a.image_refs) for c in chapters for a in c.articles),
        },
        "chapters": [
            {
                "number": ch.number,
                "title": ch.title,
                "url": ch.url,
                "status": ch.status,
                "fetch_date": ch.fetch_date,
                "article_count": len(ch.articles),
                "image_ref_count": len(ch.image_refs),
                "articles": [a.to_dict() for a in ch.articles],
            }
            for ch in chapters
        ],
    }
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    log.info("  Manifest JSON: %s", MANIFEST_JSON.name)

# ============================================================================
# Main
# ============================================================================

def main() -> None:
    ts_start = datetime.now(timezone.utc)
    log.info("=" * 60)
    log.info("Navy Uniform Regulations Scraper starting")
    log.info("Output directory: %s", CONSOLIDATED)
    log.info("Brave API key: %s", "✓ set" if os.environ.get("BRAVE_API_KEY") else "✗ not set")

    # Step 1: discover live article URLs from TOC
    discovered_urls = discover_article_urls()

    # Step 2: scrape each chapter and its articles
    chapter_records: list[ChapterRecord] = []
    for chapter in CHAPTERS:
        rec = fetch_chapter(chapter, discovered_urls)
        chapter_records.append(rec)

    # Step 3: write all output files
    log.info("Writing output files …")
    write_context_file(chapter_records)
    write_manifest_md(chapter_records)
    write_manifest_json(chapter_records)

    # Summary
    elapsed = (datetime.now(timezone.utc) - ts_start).total_seconds()
    total_arts = sum(len(c.articles) for c in chapter_records)
    ok_arts    = sum(1 for c in chapter_records for a in c.articles if a.status == "ok")
    brave_arts = sum(1 for c in chapter_records for a in c.articles if a.status == "partial")
    db_arts    = sum(1 for c in chapter_records for a in c.articles if a.status == "known_db")
    ctx_kb     = CONTEXT_FILE.stat().st_size / 1024

    log.info("=" * 60)
    log.info("Complete in %.0fs", elapsed)
    log.info("Articles: %d total | %d live | %d brave | %d known_db",
             total_arts, ok_arts, brave_arts, db_arts)
    log.info("Context file: %.1f KB → %s", ctx_kb, CONTEXT_FILE.name)
    log.info("Manifest:     %s", MANIFEST_MD.name)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
