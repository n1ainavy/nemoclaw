# Navy Policy Document Downloader

Automated tool to build and maintain a local repository of official US Navy and DoD policy documents.

## Coverage (459 documents indexed)

| # | Source | Count | Domain | Status |
|---|--------|-------|--------|--------|
| 01 | RESPERSMAN | 45 | navyreserve.navy.mil | Akamai-protected |
| 02 | MILPERSMAN | 83 | mynavyhr.navy.mil | Akamai-protected |
| 03 | SECNAV Instructions & Manuals | 66 | secnav.navy.mil | F5 WAF on listings |
| 04 | BUPERS Instructions | 27 | mynavyhr.navy.mil | Akamai-protected |
| 05 | Joint Travel Regulations (JTR) | 10 | travel.dod.mil | Network-dependent |
| 06 | DoD Directives (DoDD) | 49 | esd.whs.mil | Network-dependent |
| 07 | DoD Instructions (DoDI) | 47 | esd.whs.mil | Network-dependent |
| 08 | DoD Manuals (DoDM) | 23 | esd.whs.mil | Network-dependent |
| 09 | Directive Type Memoranda (DTM) | 14 | esd.whs.mil | Network-dependent |
| 10 | CJCS Instructions (CJCSI) | 30 | jcs.mil | Network-dependent |
| 11 | CJCS Manuals (CJCSM) | 13 | jcs.mil | Network-dependent |
| 12 | CJCS Notices (CJCSN) | 4 | jcs.mil | Network-dependent |
| 13 | Navy Regulations | 1 | secnav.navy.mil | F5 WAF |
| 14 | Uniform Regulations | 23 | mynavyhr.navy.mil | HTML/text capture |
| 15 | Career Management | 24 | mynavyhr.navy.mil | Page + PDF crawl |

## Quick Start

```bash
# Install dependencies
pip install requests beautifulsoup4 lxml

# Full dry run (builds index without downloading)
python3 downloader.py --dry-run --output ./output

# Download specific sources
python3 downloader.py --sources 01,02 --output ./output

# All sources with Brave Search API fallback
BRAVE_API_KEY=your_key python3 downloader.py --output ./output

# Auto-push to GitHub when done
GITHUB_TOKEN=ghp_xxx GITHUB_REPO=yourname/navy-policy \
  python3 downloader.py --output ./output
```

## Shell Fallback (bypasses Akamai bot detection)

```bash
# Run on a machine with unrestricted internet
BRAVE_API_KEY=your_key bash curl_downloader.sh ./output all

# Single source
bash curl_downloader.sh ./output 01   # RESPERSMAN only
```

## Output Structure

```
output/
├── 01-RESPERSMAN/         ← PDFs: RESPERSMAN_1000-010.pdf, etc.
├── 02-MILPERSMAN/         ← PDFs: MILPERSMAN_1000-010.pdf, etc.
├── 03-SECNAV-INST/        ← PDFs: SECNAVINST_1000.9D.pdf, etc.
├── 04-BUPERS-INST/        ← PDFs: BUPERSINST_1080.1D.pdf, etc.
├── 05-JTR/                ← PDFs: JTR-Full.pdf, JTR-Ch01.pdf, etc.
├── 06-DODD/               ← PDFs: DoDD_1000.01E.pdf, etc.
├── 07-DODI/               ← PDFs: DoDI_1000.01.pdf, etc.
├── 08-DODM/               ← PDFs: DoDM_1000.04.pdf, etc.
├── 09-DTM/                ← PDFs: DTM_DTM-09-026.pdf, etc.
├── 10-CJCSI/              ← PDFs: CJCSI_3121.01B.pdf, etc.
├── 11-CJCSM/              ← PDFs: CJCSM_3122.01C.pdf, etc.
├── 12-CJCSN/              ← PDFs: CJCSN_5120.pdf, etc.
├── 13-NAVREGS/            ← PDFs: NAVREGS-1990.pdf
├── 14-UNIFORM-REGS/       ← HTML + TXT per article + _COMBINED_CONTEXT.txt
├── 15-CAREER-MGMT/        ← HTML + TXT pages + any embedded PDFs
├── index.json             ← Machine-readable master index
├── index.md               ← Human-readable index (✓/⚠ per doc)
├── review_required.md     ← Manual download queue with direct URLs
└── download_log.txt       ← Verbose per-request log
```

## Using Uniform Regs as LLM Context

Source 14 saves each article as both `.html` and `.txt`, plus a combined file:

```
14-UNIFORM-REGS/_COMBINED_CONTEXT.txt   ← all articles merged, ~500KB
```

Pass this to another agent:
```python
context = Path("output/14-UNIFORM-REGS/_COMBINED_CONTEXT.txt").read_text()
# Feed to your LLM as system context or document
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `BRAVE_API_KEY` | Brave Search API key — enables PDF URL discovery when listing pages are blocked |
| `GITHUB_TOKEN` | GitHub PAT — enables auto-push after each run |
| `GITHUB_REPO` | `owner/repo` — repository to push output to |

## Notes on Network Access

- **mynavyhr.navy.mil** and **navyreserve.navy.mil** use Akamai Bot Manager. Python `requests` is blocked but `curl` often passes through due to different TLS fingerprints. Use `curl_downloader.sh`.
- **secnav.navy.mil** uses an F5 TSPD WAF on listing `.aspx` pages. Direct PDF URLs can work after a valid session cookie is established.
- **esd.whs.mil** and **jcs.mil** are accessible from open internet — the downloader will scrape live listings and download PDFs directly.
- Set `BRAVE_API_KEY` for best results — when listing pages fail, Brave Search discovers direct PDF URLs via `site:` queries.

## Updating the Known Document Lists

Edit `known_docs.py` to add or correct document entries:

```python
MILPERSMAN_ARTICLES = [
    ...
    ("1234-010", "New Article Title"),  # add here
]
```

Re-run the downloader to update the index and attempt downloads.
