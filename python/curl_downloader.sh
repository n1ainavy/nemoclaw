#!/usr/bin/env bash
# ==============================================================================
# curl_downloader.sh - Navy Policy PDF Downloader (Shell/curl fallback)
# ==============================================================================
# Run this on a machine with unrestricted internet access when Python requests
# are blocked by Akamai or other WAFs. curl's TLS fingerprint often differs
# enough from Python requests to bypass Akamai Bot Manager.
#
# Usage:
#   bash curl_downloader.sh [output_dir] [source_filter]
#   bash curl_downloader.sh ./output 01          # only RESPERSMAN
#   bash curl_downloader.sh ./output all         # everything
#
# Prerequisites:
#   curl (with TLS 1.2+ support), jq (for JSON manipulation)
#   Optional: Set BRAVE_API_KEY env var for URL discovery via Brave Search API
#
# ==============================================================================

OUTPUT_DIR="${1:-./output}"
SOURCE_FILTER="${2:-all}"
DELAY=1.5  # seconds between requests

CURL_OPTS=(
  --silent
  --show-error
  --location
  --max-time 30
  --retry 2
  --retry-delay 3
  --compressed
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
  -H "Accept-Language: en-US,en;q=0.9"
  -H "sec-ch-ua: \"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\""
  -H "sec-ch-ua-mobile: ?0"
  -H "sec-ch-ua-platform: \"Windows\""
  -H "Sec-Fetch-Dest: document"
  -H "Sec-Fetch-Mode: navigate"
  -H "Sec-Fetch-Site: none"
  -H "Sec-Fetch-User: ?1"
  --cookie-jar /tmp/navy_cookies.txt
  --cookie /tmp/navy_cookies.txt
)

REVIEW_FILE="$OUTPUT_DIR/review_required_curl.txt"
LOG_FILE="$OUTPUT_DIR/curl_download_log.txt"

mkdir -p "$OUTPUT_DIR"
echo "" > "$LOG_FILE"
echo "# URLs requiring manual download" > "$REVIEW_FILE"
echo "# Generated: $(date)" >> "$REVIEW_FILE"
echo "" >> "$REVIEW_FILE"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }

# ------------------------------------------------------------------------------
# Core download function
# ------------------------------------------------------------------------------
download_pdf() {
  local url="$1"
  local dest="$2"
  local name="$3"

  mkdir -p "$(dirname "$dest")"

  # Skip if already downloaded
  if [[ -f "$dest" ]] && [[ $(stat -c%s "$dest" 2>/dev/null || echo 0) -gt 1000 ]]; then
    log "  SKIP (exists): $name"
    return 0
  fi

  sleep "$DELAY"
  local tmp=$(mktemp /tmp/navy_dl_XXXXXX)

  # First request to get any session cookies
  curl "${CURL_OPTS[@]}" -o /dev/null "$url" 2>/dev/null
  sleep 0.5

  # Second request (now with cookies) to download
  local http_code
  http_code=$(curl "${CURL_OPTS[@]}" -o "$tmp" -w "%{http_code}" "$url" 2>>"$LOG_FILE")

  # Check if it is a real PDF
  if [[ "$http_code" == "200" ]] && head -c 4 "$tmp" 2>/dev/null | grep -q '%PDF'; then
    mv "$tmp" "$dest"
    local size
    size=$(stat -c%s "$dest" 2>/dev/null || wc -c < "$dest")
    log "  ✓ Downloaded ($size bytes): $name"
    return 0
  else
    rm -f "$tmp"
    log "  ✗ Failed (HTTP $http_code): $name"
    echo "- [$name]($url)" >> "$REVIEW_FILE"
    return 1
  fi
}

# ------------------------------------------------------------------------------
# Scrape a listing page and extract all PDF links
# ------------------------------------------------------------------------------
scrape_and_download() {
  local listing_url="$1"
  local dest_dir="$2"
  local source_name="$3"

  log "Scraping: $listing_url"
  sleep "$DELAY"

  local html
  html=$(curl "${CURL_OPTS[@]}" "$listing_url" 2>>"$LOG_FILE")
  local http_code=$?

  # Check for WAF/access denied
  if echo "$html" | grep -qi "access denied\|request rejected\|captcha\|support id"; then
    log "  WAF/403 on listing page: $listing_url"
    echo "## $source_name listing page blocked" >> "$REVIEW_FILE"
    echo "- $listing_url" >> "$REVIEW_FILE"
    return 1
  fi

  # Extract PDF links
  local pdf_links
  pdf_links=$(echo "$html" | grep -oP 'href="[^"]*\.pdf[^"]*"' | sed 's/href="//;s/"//')

  local count=0
  while IFS= read -r href; do
    [[ -z "$href" ]] && continue
    # Resolve relative URLs
    if [[ "$href" == http* ]]; then
      local full_url="$href"
    else
      # Combine base URL with relative path
      local base_url
      base_url=$(echo "$listing_url" | grep -oP '^https?://[^/]+')
      if [[ "$href" == /* ]]; then
        full_url="${base_url}${href}"
      else
        local base_path
        base_path=$(echo "$listing_url" | sed 's|/[^/]*$|/|')
        full_url="${base_path}${href}"
      fi
    fi

    local filename
    filename=$(basename "$href" | sed 's/[?#].*//')
    local dest="$dest_dir/$filename"

    download_pdf "$full_url" "$dest" "$filename"
    ((count++))
  done <<< "$pdf_links"

  log "  → Processed $count PDF links from $source_name"
}

# ------------------------------------------------------------------------------
# Brave Search API - discover PDF URLs when listing pages are blocked
# ------------------------------------------------------------------------------
brave_search_pdfs() {
  local query="$1"
  local dest_dir="$2"
  local source_name="$3"

  if [[ -z "$BRAVE_API_KEY" ]]; then
    log "  BRAVE_API_KEY not set – skipping Brave search for: $query"
    return 1
  fi

  log "  Brave Search: $query"

  local search_url="https://api.search.brave.com/res/v1/web/search?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")&count=20&search_lang=en&freshness=pw"

  local results
  results=$(curl --silent --max-time 15 \
    -H "Accept: application/json" \
    -H "Accept-Encoding: gzip" \
    -H "X-Subscription-Token: $BRAVE_API_KEY" \
    "$search_url" 2>/dev/null)

  if [[ -z "$results" ]]; then
    log "  Brave search returned no results"
    return 1
  fi

  # Extract .pdf URLs from Brave results
  local pdf_urls
  pdf_urls=$(echo "$results" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for result in data.get('web', {}).get('results', []):
        url = result.get('url', '')
        if '.pdf' in url.lower() and 'navy.mil' in url.lower():
            print(url)
except: pass
" 2>/dev/null)

  local count=0
  while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    local filename
    filename=$(basename "$url" | sed 's/[?#].*//')
    download_pdf "$url" "$dest_dir/$filename" "$filename"
    ((count++))
  done <<< "$pdf_urls"

  log "  → Found $count PDF URLs via Brave search"
}

# ------------------------------------------------------------------------------
# GitHub push function
# ------------------------------------------------------------------------------
push_to_github() {
  local repo_path="$1"
  local commit_msg="Auto-update Navy policy documents $(date +%Y-%m-%d)"

  if [[ ! -d "$repo_path/.git" ]]; then
    log "Not a git repo: $repo_path"
    return 1
  fi

  cd "$repo_path" || return 1
  git add -A
  git commit -m "$commit_msg"
  git push origin main
  log "Pushed to GitHub: $repo_path"
}

# ==============================================================================
# SOURCE-SPECIFIC SCRAPERS
# ==============================================================================

scrape_01_respersman() {
  local dir="$OUTPUT_DIR/01-RESPERSMAN"
  mkdir -p "$dir"
  log "=== 01 RESPERSMAN ==="

  scrape_and_download \
    "https://www.navyreserve.navy.mil/Resources/Official-RESFOR-Guidance/RESPERSMAN/" \
    "$dir" "RESPERSMAN"

  # Fallback: Brave API search
  brave_search_pdfs \
    "site:navyreserve.navy.mil RESPERSMAN filetype:pdf" \
    "$dir" "RESPERSMAN"
}

scrape_02_milpersman() {
  local dir="$OUTPUT_DIR/02-MILPERSMAN"
  mkdir -p "$dir"
  log "=== 02 MILPERSMAN ==="

  scrape_and_download \
    "https://www.mynavyhr.navy.mil/References/MILPERSMAN/" \
    "$dir" "MILPERSMAN"

  brave_search_pdfs \
    "site:mynavyhr.navy.mil MILPERSMAN filetype:pdf" \
    "$dir" "MILPERSMAN"
}

scrape_03_secnav() {
  local dir="$OUTPUT_DIR/03-SECNAV-INST"
  mkdir -p "$dir"
  log "=== 03 SECNAV INSTRUCTIONS ==="

  for page in "manuals-secnav.aspx" "navyinstructions.aspx" "allissuances.aspx"; do
    scrape_and_download \
      "https://www.secnav.navy.mil/doni/$page" \
      "$dir" "SECNAV-$page"
  done

  brave_search_pdfs \
    "site:secnav.navy.mil SECNAVINST filetype:pdf" \
    "$dir" "SECNAVINST"
}

scrape_04_bupers() {
  local dir="$OUTPUT_DIR/04-BUPERS-INST"
  mkdir -p "$dir"
  log "=== 04 BUPERS INSTRUCTIONS ==="

  scrape_and_download \
    "https://www.mynavyhr.navy.mil/References/BUPERS-Instructions/" \
    "$dir" "BUPERSINST"

  brave_search_pdfs \
    "site:mynavyhr.navy.mil BUPERSINST filetype:pdf" \
    "$dir" "BUPERSINST"
}

scrape_05_jtr() {
  local dir="$OUTPUT_DIR/05-JTR"
  mkdir -p "$dir"
  log "=== 05 JTR (travel.dod.mil - may be blocked) ==="

  scrape_and_download \
    "https://www.travel.dod.mil/Policy-Regulations/Joint-Travel-Regulations/" \
    "$dir" "JTR"

  # Direct known PDF URLs
  local jtr_base="https://www.travel.dod.mil/Portals/119/Documents/JTR"
  for chapter in "JTR_Chapter_01" "JTR_Chapter_02" "JTR_Chapter_03" \
                 "JTR_Chapter_04" "JTR_Chapter_05" "JTR_Chapter_06" \
                 "JTR_Appendix_A" "JTR_Appendix_B" "JTR_Appendix_C" \
                 "Joint_Travel_Regulations"; do
    download_pdf "$jtr_base/$chapter.pdf" "$dir/$chapter.pdf" "JTR $chapter"
  done
}

scrape_06_dodd() {
  local dir="$OUTPUT_DIR/06-DODD"
  mkdir -p "$dir"
  log "=== 06 DoD DIRECTIVES (esd.whs.mil) ==="
  scrape_and_download "https://www.esd.whs.mil/Directives/issuances/dodd/" "$dir" "DoDD"
  brave_search_pdfs "site:esd.whs.mil DoDD filetype:pdf" "$dir" "DoDD"
}

scrape_07_dodi() {
  local dir="$OUTPUT_DIR/07-DODI"
  mkdir -p "$dir"
  log "=== 07 DoD INSTRUCTIONS (esd.whs.mil) ==="
  scrape_and_download "https://www.esd.whs.mil/Directives/issuances/dodi/" "$dir" "DoDI"
  brave_search_pdfs "site:esd.whs.mil DoDI filetype:pdf" "$dir" "DoDI"
}

scrape_08_dodm() {
  local dir="$OUTPUT_DIR/08-DODM"
  mkdir -p "$dir"
  log "=== 08 DoD MANUALS (esd.whs.mil) ==="
  scrape_and_download "https://www.esd.whs.mil/Directives/issuances/dodm/" "$dir" "DoDM"
}

scrape_09_dtm() {
  local dir="$OUTPUT_DIR/09-DTM"
  mkdir -p "$dir"
  log "=== 09 DTM (esd.whs.mil) ==="
  scrape_and_download "https://www.esd.whs.mil/DD/DoD-Issuances/DTM/" "$dir" "DTM"
}

scrape_10_cjcsi() {
  local dir="$OUTPUT_DIR/10-CJCSI"
  mkdir -p "$dir"
  log "=== 10 CJCSI (jcs.mil) ==="
  scrape_and_download "https://www.jcs.mil/library/cjcs-instructions/" "$dir" "CJCSI"
  brave_search_pdfs "site:jcs.mil CJCSI filetype:pdf" "$dir" "CJCSI"
}

scrape_11_cjcsm() {
  local dir="$OUTPUT_DIR/11-CJCSM"
  mkdir -p "$dir"
  log "=== 11 CJCSM (jcs.mil) ==="
  scrape_and_download "https://www.jcs.mil/Library/CJCS-Manuals/" "$dir" "CJCSM"
}

scrape_12_cjcsn() {
  local dir="$OUTPUT_DIR/12-CJCSN"
  mkdir -p "$dir"
  log "=== 12 CJCSN (jcs.mil) ==="
  scrape_and_download "https://www.jcs.mil/Library/CJCS-Notices/" "$dir" "CJCSN"
}

scrape_13_navregs() {
  local dir="$OUTPUT_DIR/13-NAVREGS"
  mkdir -p "$dir"
  log "=== 13 NAVY REGULATIONS ==="

  scrape_and_download \
    "https://www.secnav.navy.mil/doni/navyregs.aspx" \
    "$dir" "NavyRegs"

  # Direct URL for the main Navy Regulations document
  download_pdf \
    "https://www.secnav.navy.mil/doni/Regulations/US%20Navy%20Regulations%201990.pdf" \
    "$dir/US_Navy_Regulations_1990.pdf" \
    "US Navy Regulations 1990"
}

scrape_14_uniform() {
  local dir="$OUTPUT_DIR/14-UNIFORM-REGS"
  mkdir -p "$dir"
  log "=== 14 UNIFORM REGULATIONS ==="

  local toc_url="https://www.mynavyhr.navy.mil/References/US-Navy-Uniforms/Uniform-Regulations/Table-of-Contents/"
  local html
  html=$(curl "${CURL_OPTS[@]}" "$toc_url" 2>/dev/null)

  if echo "$html" | grep -qi "access denied\|request rejected"; then
    log "  Uniform Regs TOC blocked"
    echo "## Uniform Regulations - All articles need manual download" >> "$REVIEW_FILE"
    echo "- TOC: $toc_url" >> "$REVIEW_FILE"
    return
  fi

  # Save TOC itself
  echo "$html" > "$dir/table_of_contents.html"
  log "  Saved TOC page"

  # Extract article links
  local article_links
  article_links=$(echo "$html" | grep -oP 'href="[^"]*uniform-regulations[^"]*"' | sed 's/href="//;s/"//')

  while IFS= read -r href; do
    [[ -z "$href" ]] && continue
    local full_url
    if [[ "$href" == http* ]]; then full_url="$href"
    else full_url="https://www.mynavyhr.navy.mil$href"; fi

    local article_name
    article_name=$(echo "$href" | sed 's|.*/||;s|/$||' | tr '/' '_')
    [[ -z "$article_name" ]] && article_name="article_$(date +%s%N)"

    sleep "$DELAY"
    local article_html
    article_html=$(curl "${CURL_OPTS[@]}" "$full_url" 2>/dev/null)

    if ! echo "$article_html" | grep -qi "access denied"; then
      echo "$article_html" > "$dir/${article_name}.html"
      # Extract plain text
      echo "$article_html" | sed 's/<[^>]*>//g' | tr -s ' \t\n' ' ' > "$dir/${article_name}.txt"
      log "  ✓ Saved article: $article_name"

      # Download any PDFs in the article
      local pdfs
      pdfs=$(echo "$article_html" | grep -oP 'href="[^"]*\.pdf[^"]*"' | sed 's/href="//;s/"//')
      while IFS= read -r pdf_href; do
        [[ -z "$pdf_href" ]] && continue
        local pdf_url
        if [[ "$pdf_href" == http* ]]; then pdf_url="$pdf_href"
        else pdf_url="https://www.mynavyhr.navy.mil$pdf_href"; fi
        local pdf_name
        pdf_name=$(basename "$pdf_href" | sed 's/[?#].*//')
        download_pdf "$pdf_url" "$dir/$pdf_name" "$pdf_name"
      done <<< "$pdfs"
    else
      log "  ✗ Blocked: $article_name"
      echo "- [$article_name]($full_url)" >> "$REVIEW_FILE"
    fi
  done <<< "$article_links"

  # Combine all text files into a single context file for LLM use
  log "  Building combined context file..."
  cat "$dir"/*.txt > "$dir/_combined_uniform_regs_context.txt" 2>/dev/null
  log "  ✓ Combined context: $dir/_combined_uniform_regs_context.txt"
}

scrape_15_career() {
  local dir="$OUTPUT_DIR/15-CAREER-MGMT"
  mkdir -p "$dir"
  log "=== 15 CAREER MANAGEMENT ==="

  local base="https://www.mynavyhr.navy.mil"
  declare -a sections=(
    "Career-Management/"
    "Career-Management/Enlisted/"
    "Career-Management/Enlisted/Advancement/"
    "Career-Management/Enlisted/Assignment/"
    "Career-Management/Enlisted/Reenlistment/"
    "Career-Management/Enlisted/Retention/"
    "Career-Management/Officer/"
    "Career-Management/Officer/Advancement/"
    "Career-Management/Officer/Assignment/"
    "Career-Management/Officer/Promotions/"
    "Career-Management/Training-Education/"
    "Career-Management/Training-Education/Voluntary-Education/"
    "Career-Management/Awards/"
    "Career-Management/Separations/"
    "Career-Management/Retirement/"
    "Career-Management/Family-Support/"
    "Career-Management/Legal/"
    "Career-Management/Physical-Readiness/"
    "Career-Management/Navy-College/"
    "Career-Management/Leave/"
    "Career-Management/Pay-Benefits/"
    "Career-Management/Records/"
  )

  local all_pdfs=()

  for section in "${sections[@]}"; do
    local url="$base/$section"
    local safe_name
    safe_name=$(echo "$section" | sed 's|/|_|g;s|_$||')
    local html_file="$dir/${safe_name}.html"

    sleep "$DELAY"
    local html
    html=$(curl "${CURL_OPTS[@]}" "$url" 2>/dev/null)

    if echo "$html" | grep -qi "access denied\|request rejected"; then
      log "  ✗ Blocked: $section"
      echo "- [$section]($url)" >> "$REVIEW_FILE"
      continue
    fi

    echo "$html" > "$html_file"
    echo "$html" | sed 's/<[^>]*>//g' | tr -s ' \t\n' '\n' > "${html_file%.html}.txt"
    log "  ✓ Saved section: $section"

    # Collect PDF links
    while IFS= read -r pdf_href; do
      [[ -z "$pdf_href" ]] && continue
      local pdf_url
      if [[ "$pdf_href" == http* ]]; then pdf_url="$pdf_href"
      else pdf_url="${base}${pdf_href}"; fi
      all_pdfs+=("$pdf_url")
    done < <(echo "$html" | grep -oP 'href="[^"]*\.pdf[^"]*"' | sed 's/href="//;s/"//')
  done

  # Download all collected PDFs (deduplicated)
  local unique_pdfs
  printf '%s\n' "${all_pdfs[@]}" | sort -u | while IFS= read -r pdf_url; do
    [[ -z "$pdf_url" ]] && continue
    local pdf_name
    pdf_name=$(basename "$pdf_url" | sed 's/[?#].*//')
    download_pdf "$pdf_url" "$dir/$pdf_name" "$pdf_name"
  done
}

# ==============================================================================
# MAIN
# ==============================================================================
log "Navy Policy Downloader (curl) starting"
log "Output: $OUTPUT_DIR | Filter: $SOURCE_FILTER"
mkdir -p "$OUTPUT_DIR"

run_source() {
  local num="$1"
  if [[ "$SOURCE_FILTER" == "all" ]] || [[ "$SOURCE_FILTER" == "$num"* ]]; then
    "scrape_${num}_$2"
  fi
}

run_source "01" "respersman"
run_source "02" "milpersman"
run_source "03" "secnav"
run_source "04" "bupers"
run_source "05" "jtr"
run_source "06" "dodd"
run_source "07" "dodi"
run_source "08" "dodm"
run_source "09" "dtm"
run_source "10" "cjcsi"
run_source "11" "cjcsm"
run_source "12" "cjcsn"
run_source "13" "navregs"
run_source "14" "uniform"
run_source "15" "career"

# Push to GitHub if configured
if [[ -n "$GITHUB_REPO_PATH" ]]; then
  push_to_github "$GITHUB_REPO_PATH"
fi

log "Done. Review file: $REVIEW_FILE"
