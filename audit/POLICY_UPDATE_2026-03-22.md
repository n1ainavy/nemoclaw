# Policy Source Update Check — 2026-03-22

**Run type:** Scheduled weekly check (automated — Claude Cowork)
**Date:** 22 March 2026
**Scope:** Scan of 15 official DoD/Navy policy sources for recent publications, new issuances, and supersession actions.

---

## Access Status by Source

Several .mil domains are blocked by the network egress proxy and could not be directly fetched. Web search was used as a fallback to identify recent publications. The table below documents access results.

| Source URL | Access Status |
|---|---|
| secnav.navy.mil/doni/allinstructions.aspx | ❌ WAF block (URL rejected) |
| secnav.navy.mil/doni/manuals-secnav.aspx | ❌ WAF block |
| secnav.navy.mil/doni/manuals-opnav.aspx | ❌ WAF block |
| mynavyhr.navy.mil/References/BUPERS-Instructions/ | ❌ HTTP 403 |
| travel.dod.mil/Policy-Regulations/Joint-Travel-Regulations/ | ❌ EGRESS_BLOCKED |
| esd.whs.mil/DD/Recent-Publications/ | ❌ EGRESS_BLOCKED |
| esd.whs.mil/Directives/issuances/dodd/ | ❌ EGRESS_BLOCKED |
| esd.whs.mil/Directives/issuances/dodi/ | ❌ EGRESS_BLOCKED |
| esd.whs.mil/Directives/issuances/dodm/ | ❌ EGRESS_BLOCKED |
| esd.whs.mil/DD/DoD-Issuances/DTM/ | ❌ EGRESS_BLOCKED |
| jcs.mil/Library/CJCS-Instructions/ | ❌ EGRESS_BLOCKED |
| jcs.mil/Library/CJCS-Manuals/ | ❌ EGRESS_BLOCKED |
| jcs.mil/Library/CJCS-Notices/ | ❌ EGRESS_BLOCKED |
| mynavyhr.navy.mil/References/Messages/NAVADMIN-2026/ | ❌ HTTP 403 |
| mynavyhr.navy.mil/References/Messages/ALNAV-2026/ | ❌ HTTP 403 |

> **Note:** All 15 source URLs are currently inaccessible via WebFetch due to WAF restrictions or egress proxy blocks. The findings below were compiled through targeted web searches against indexed .mil content and cached PDF metadata. Direct link verification is not possible in this environment. The user should verify directly against official portals (CAC-authenticated access recommended).

---

## Recent Publications Found — By Source

### 1. SECNAV / OPNAV Instructions (secnav.navy.mil/doni)

| Doc Number | Title | Date | Supersedes |
|---|---|---|---|
| OPNAVINST 1420.1C | Enlisted to Officer Commissioning Programs — Unrestricted Line, Special Duty Line, and Staff Corps Communities | 5 Mar 2026 | OPNAVINST 1420.1B (14 Dec 2009) |

- **Source confirmed:** PDF indexed at secnav.navy.mil/doni/Directives/01000.../1420.1C.pdf
- **Notes:** Includes enclosures for Officer Programs Application (OPNAV 1420/1), USNA Applicant Checklist, and STA-21 checklist. Effective 10 years unless revised or cancelled.

---

### 2. SECNAV Manuals (secnav.navy.mil/doni/manuals-secnav.aspx)

No new SECNAV Manual publications identified via web search for the current weekly period (week of 15–22 March 2026). Source blocked; manual review recommended.

---

### 3. OPNAV Manuals (secnav.navy.mil/doni/manuals-opnav.aspx)

No new OPNAV Manual publications identified via web search for the current weekly period. Source blocked; manual review recommended.

---

### 4. BUPERS Instructions (mynavyhr.navy.mil/References/BUPERS-Instructions/)

| Doc Number | Title | Date | Supersedes |
|---|---|---|---|
| BUPERSINST 1430.16H | Advancement Manual for Enlisted Personnel of the U.S. Navy and U.S. Navy Reserve | 21 Jan 2026 | BUPERSINST 1430.16G; cancels multiple NAVADMINs incl. 221/25, 316/18, 313/18, 312/18 |

- **Notes:** Establishes Billet-Based Advancement (BBA) as primary framework. Nearly all active-duty E-6 ratings now in BBA; 14 ratings fully integrated E-5 through E-9. Previously integrated into this repo (finalized/10-advancement/) as of AUDIT_2026-03-22b.

---

### 5. Joint Travel Regulations (travel.dod.mil)

| Doc | Version / Date | Notes |
|---|---|---|
| Joint Travel Regulations (JTR) | Effective 01 Mar 2026 | Updated per FY2026 NDAA Section 377 — authorizes non-U.S. flag carriers for pet transport when no U.S. flag carrier is available |

- **Source:** JTR is maintained as a living document updated via numbered change pages. The current effective version is dated 01 Mar 2026 (MAP-CAP 04-26(S) reflected).
- **Repo status:** JTR PDF is in finalized/08-travel/ — may require refresh if content has changed since last pull.

---

### 6. DoD Recent Publications / Directives Division (esd.whs.mil) — DoDD / DoDI / DoDM / DTM

All esd.whs.mil URLs are egress-blocked. Findings below are from web search against indexed PDF metadata:

#### DoD Instructions (DoDI)

| Doc Number | Title | Date | Supersedes |
|---|---|---|---|
| DoWI 5025.01 | DoW Issuances Program | 20 Jan 2026 | DoDI 5025.01 (1 Aug 2016) |

- **Notes:** Formally reissues and cancels DoDI 5025.01. Establishes updated policy, responsibilities, and procedures for development, coordination, approval, publication, and review of DoD issuances. Style guide updated 21 Jan 2026 and 12 Feb 2026 to comply.

#### Directive-Type Memoranda (DTM) — Active with 2026 Expiration

| DTM Number | Title | Effective | Expires |
|---|---|---|---|
| DTM 25-003 | Implementing the DoD Zero Trust Strategy | 17 Jul 2025 | 17 Jul 2026 |
| DTM 25-004 | DoD Suicide Postvention Response System | 24 Jul 2025 | 24 Jul 2026 |
| DTM 24-004 | Facility-Related Policy (exact title blocked) | 2024 | 31 Jul 2026 (extended) |
| DTM 18-003 | Prohibition on Providing Funds to the Enemy / Additional Access to Records | 2018 | 11 Aug 2026 (extended) |

- **Notes:** DTMs are interim issuances to be incorporated into permanent issuances, converted to new issuances, reissued, or cancelled. The above are active DTMs with 2026 expiration dates that should be monitored.

#### DoD Directives (DoDD) and DoD Manuals (DoDM)

No new DoDD or DoDM publications were identified via web search for the current weekly period. Source blocked; manual review recommended.

---

### 7. CJCS Instructions (jcs.mil/Library/CJCS-Instructions/)

| Doc Number | Title | Date | Supersedes |
|---|---|---|---|
| CJCSI 5123.01J | Charter of the Joint Requirements Oversight Council | 15 Jan 2026 | CJCSI 5123.01I; cancels JROCM 102-05 (20 May 2005) |

- **Notes:** Fundamentally reorients the JROC — removes validation of Service/component-level requirements; refocuses on Joint Force Development (JFD), Joint Capability Integration (JCI), and CCMD requirements. Introduces the Joint Force Requirements Process (JFRP) as a replacement for aspects of JCIDS. Previously validated JROC requirements and signed JROCMs remain in effect.

---

### 8. CJCS Manuals (jcs.mil/Library/CJCS-Manuals/)

| Doc Number | Title | Date | Supersedes |
|---|---|---|---|
| CJCSM 5123.01 | Manual for the Joint Requirements Oversight Council and the Joint Force Requirements Process | 15 Jan 2026 | "Manual for the Operation of the JCIDS" (30 Oct 2021) |

- **Notes:** Companion document to CJCSI 5123.01J. Replaces JCIDS with the Joint Force Requirements Process (JFRP) in its entirety.

---

### 9. CJCS Notices (jcs.mil/Library/CJCS-Notices/)

No new CJCS Notices identified via web search for the current weekly period. Source egress-blocked; manual review recommended.

---

### 10. NAVADMIN 2026 (mynavyhr.navy.mil/References/Messages/NAVADMIN-2026/)

Source is HTTP 403. Individual message PDFs on mynavyhr.navy.mil portals are also 403. The following NAVADMINs were identified via indexed web search metadata:

| Message | Date (DTG) | Subject | Supersedes / Notes |
|---|---|---|---|
| NAVADMIN 008/26 | 13 Jan 2026 | Cycle 271 Navy-Wide Advancement Exams (NWAE) / Rating Knowledge Exams (RKE) — Active Duty and TAR E-5 | Guidance only; no prior NAVADMIN explicitly cancelled |
| NAVADMIN 038/26 | 25 Feb 2026 | Officer Promotions — Authority for Permanent Officer Promotions | Congratulatory/authority message; promotion dates specified |
| NAVADMIN 051/26 | 9 Mar 2026 | Subject not confirmed via search (PDF blocked) | — |

> **Note:** Only messages visible through search engine indexing are captured above. The full FY2026 NAVADMIN list (NAV26001–NAV26051+ as of report date) requires direct portal access. Confirmed messages with known subjects are listed; others existed but subjects could not be verified.

---

### 11. ALNAV 2026 (mynavyhr.navy.mil/References/Messages/ALNAV-2026/)

Source is HTTP 403. No individual ALNAV messages were surfaced via web search for 2026. ALNAV messages originate from SECNAV and are typically issued for Service-wide policy changes, appointments, and designations.

> **No ALNAV 2026 messages could be confirmed through available search tools.** Direct portal access (CAC or NIPRNet) is required to enumerate the 2026 ALNAV list.

---

## Repository Impact Assessment

| Finding | Impact on Repo | Priority |
|---|---|---|
| OPNAVINST 1420.1C (5 Mar 2026) | Not currently in repo; may be relevant for Career Management category | LOW–MEDIUM |
| BUPERSINST 1430.16H | Already integrated (finalized/10-advancement/) | ✅ COMPLETE |
| JTR effective 01 Mar 2026 | JTR PDF in finalized/08-travel/ — verify if current | MEDIUM |
| CJCSI 5123.01J / CJCSM 5123.01 (15 Jan 2026) | Not currently in repo; JROC/JCIDS docs not tracked | LOW |
| DoWI 5025.01 (20 Jan 2026) | Issuances program management — not tracked in repo | LOW |
| Active DTMs with 2026 expiration | DTM 24-004, 25-003, 25-004, 18-003 — not tracked | INFORMATIONAL |
| NAVADMIN 2026 messages | finalized/13-navadmin/ category exists; current content unknown | REVIEW NEEDED |
| ALNAV 2026 | Not tracked in repo | LOW |

---

## Recommended Actions

1. **JTR Review (MEDIUM):** Verify the JTR PDF in finalized/08-travel/ reflects the 01 Mar 2026 effective version. Pull the latest JTR from travel.dod.mil if accessible via CAC/NIPRNet.

2. **NAVADMIN Category Review (MEDIUM):** Access mynavyhr.navy.mil directly (CAC authenticated) to enumerate the full NAV26001–NAV26051+ list and update finalized/13-navadmin/ as appropriate.

3. **OPNAVINST 1420.1C (LOW–MEDIUM):** If officer commissioning programs are in scope, download from secnav.navy.mil/doni and place in an appropriate finalized/ folder (e.g., 10-advancement or a new 14-commissioning category).

4. **NAVPERS 15665J (OPEN from prior audit):** Still unresolved per AUDIT_2026-03-22b Section 9. Download from mynavyhr.navy.mil Uniform Regulations page.

5. **Network Access:** All 15 source URLs are currently blocked by the egress proxy. Consider running this check from a NIPRNet-connected workstation or via CAC-authenticated browser session for complete coverage.

---

## Sources Used

- [NAVADMIN 2026 — MyNavyHR](https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN-2026/)
- [ALNAV 2026 — MyNavyHR](https://www.mynavyhr.navy.mil/References/Messages/ALNAV-2026/)
- [BUPERS Instructions — MyNavyHR](https://www.mynavyhr.navy.mil/References/BUPERS-Instructions/)
- [BUPERSINST 1430.16H PDF](https://www.mynavyhr.navy.mil/Portals/55/Reference/Instructions/BUPERS/BUPERSINST%201430.16.pdf)
- [OPNAVINST 1420.1C PDF](https://www.secnav.navy.mil/doni/Directives/01000%20Military%20Personnel%20Support/01-400%20Promotion%20and%20Advancement%20Programs/1420.1C.pdf)
- [DoD Directives Division — Recent Publications](https://www.esd.whs.mil/Directives/Recent-Publications/)
- [DoWI 5025.01 PDF](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/502501p.pdf)
- [DTM 25-004](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dtm/DTM-25-004.PDF)
- [CJCSI 5123.01J PDF](https://www.jcs.mil/Portals/36/Documents/Library/Instructions/CJCSI%205123.01J.pdf)
- [CJCSM 5123.01 PDF](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/CJCSM%205123.01.pdf)
- [Joint Travel Regulations — DTMO](https://www.travel.dod.mil/Policy-Regulations/Joint-Travel-Regulations/)
- [DVIDS — Navy Updates Enlisted Advancement Manual](https://www.dvidshub.net/news/557059/navy-updates-enlisted-advancement-manual-sailors-need-know)

---

*Report generated by automated scheduled task (Claude Cowork) — 22 March 2026. Direct portal access to all 15 source URLs was unavailable in this environment; findings are based on web search indexing of .mil content. Full accuracy requires NIPRNet/CAC-authenticated verification.*
