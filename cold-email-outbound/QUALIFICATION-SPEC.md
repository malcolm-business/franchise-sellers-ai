# Cold Email — Qualification & Enrichment Spec

**Source:** Theodore, 2026-06-25 (the rules he previously ran in a Clay table). This is the canonical "who do we contact, under which brand" spec. Complements `03-brands-and-icp.md` and feeds `engine/scoring.py` + `engine/audiences.py` + a new qualification stage.

The rules fall into three jobs — keep them separate in code:

- **FILTER** — hard include/exclude (drop the unqualified before we spend a cent or send).
- **TARGET** — slice a campaign (industry, geography).
- **ROUTE** — decide which brand / offer a qualified lead belongs to.

---

## Brand model (read this first)

A lead resolves to one of three outcomes:

| Outcome | What it is | Fit rules |
|---|---|---|
| **FS — Franchise Sellers** | A franchise business (incl. franchise-with-a-DBA that *looks* private) | Any franchise is a fit **except** > 25 locations (too big for now). We have the Toolkit for them. |
| **CS — Full Service** *(the focus)* | A bigger, qualified **private** business | The "bigger quality seller leads." Must pass the CS qualifiers below. |
| **CS — Toolkit** *(deprioritized)* | A smaller private business | We'll sell the Toolkit to them, but we do **not** focus outreach here. |

> The hard part: a franchise with a DBA looks like a private business. Brand detection (ROUTE) must catch that, or we email the wrong brand with the wrong offer. **High priority.**

---

## The rules

Legend — **Job**: Filter / Target / Route · **Data**: where the signal comes from · **Stage**: when we evaluate it (cheap → expensive funnel below).

| # | Rule | Job | Applies | Data source | Stage | Priority |
|---|------|-----|---------|-------------|-------|----------|
| 1 | **Industry** must be verified (real industry of the business) | Target | both | pool field → LeadMagic company → AI from site/LinkedIn | 1–2 | High |
| 2 | **Revenue ≤ $25M/yr** — CS upper limit *(confirmed 2026-06-25; no stated minimum)* | Filter | CS | company enrichment (hard data); employee-count proxy first | 2–3 | Med (data-limited) |
| 3 | **Employees ≤ 50** (over 50 = too big for now) | Filter | CS | LeadMagic company size *(already captured)* | 1 | **High (cheap)** |
| 4 | **Franchise locations ≤ 25** (over 25 = too big) | Filter | FS | franchise research / AI | 3 | Med (data-limited) |
| 5 | **Privately held · no public co · no PE** (both) — and **single owner / ≤ 3 owners** (CS only) | Filter | both / CS | AI + markers (ticker, "Holdings", PE portfolio lists) | 2–3 | **High (PE/public exclusion)** |
| 6 | **Location** campaigns — target a radius around a point (e.g. "business for sale in SoCal") | Target | both | geocode city/zip → lat-lng + radius | 1 (when run) | Med (campaign feature) |
| 7 | **US business only** — can't sell businesses outside the USA | Filter | both | pool `country` field → enrichment | 0 | **Critical (cheap)** |
| 8 | **Correct brand** — franchise vs private (catch franchise-with-DBA) | Route | both | franchise-system keyword match *(have it)* + AI | 1–2 | **Critical** |
| 9 | **Business age ≥ 3 yrs** (so they have real financials to value/sell) | Filter | CS | LeadMagic `company_founded` *(already captured)* | 1 | **High (cheap)** |
| 10 | **Current owner** — NOT retired, did NOT already sell. The person is the *current* owner. | Filter | both | AI reads LinkedIn: are they currently at this company as owner? | 2 | **CRITICAL** |
| 11 | **Owner located in the US** — US business but foreign owner = too hard to work | Filter | both | LinkedIn / enrichment owner location | 2 | High |

---

## How we build it — the cheap → expensive funnel

The whole trick (this is what Clay did with credits) is **never run an expensive check on a lead a cheap check already killed.** Each stage only sees survivors of the prior one.

**Stage 0 — Free filters on data we already have** (no API spend)
US-only (#7), geography (#6), has-industry (#1 presence), drop already-excluded companies (real-estate etc.). Kills the obviously-wrong before any cost.

**Stage 1 — Company enrichment** (LeadMagic — *already wired into verification*)
Returns verified industry, **employee count**, **founding year**, LinkedIn company. Apply the cheap structured filters here: employees ≤ 50 (#3), age ≥ 3 yrs (#9), industry (#1), first-pass brand via franchise-keyword match (#8).

**Stage 2 — AI judgment on survivors** (Claude, ~$0.001–0.005/lead — the "Clay AI column")
The reasoning calls that need a model to read a profile/site: **current-owner-still-active (#10)**, owner-in-US (#11), franchise-vs-private incl. DBA (#8 final), privately-held / no-PE-no-public / owner-count (#5). Only runs on Stage-0/1 survivors, so the spend stays small.

**Stage 3 — Hard-to-source data** (only if needed, on the short list)
Revenue band (#2), franchise location count (#4). These are the weakest data points industry-wide; for now use employee count as the revenue proxy and accept partial coverage.

**Stage 4 — Email verify** (LeadMagic → ZeroBounce) — only on fully-qualified leads.

Each lead ends with a **`qualification` result** on the Contact: `{qualified: bool, brand: FS|CS, product: full_service|toolkit, reasons: [...], failed_rule: "..."}` — the equivalent of Clay's `qualification_status` column. Stored so it's auditable and re-runnable.

---

## Priority call — what's important vs not

**Tier 1 — do first (protect the brand + cheap wins):**
- **#10 current owner** + **#8 correct brand** + **#7 US business / #11 US owner** + **#5 exclude PE/public** → these prevent the *embarrassing, conversion-killing* misses.
- **#3 employees ≤ 50**, **#9 age ≥ 3 yrs** → nearly free (LeadMagic already returns them).

**Tier 2 — valuable, moderate effort:**
- **#1 industry verification** (needed for industry campaigns), **#6 geo-radius** (build when the first location campaign is needed), **owner-count ≤ 3**.

**Tier 3 — hard / data-limited (later or partial):**
- **#2 revenue band**, **#4 franchise location count** — weakest data; proxy with employee count, enrich only the short list.

---

## Open questions to confirm (don't block — flagged so we lock them later)

1. ~~Revenue max~~ — **CONFIRMED 2026-06-25: CS ≤ $25M/yr**, no stated minimum (no hard floor unless Theodore adds one).
2. ~~Caps scope~~ — **CONFIRMED 2026-06-25: employee ≤50 + revenue ≤$25M caps are CS-only** (FS uses the ≤25-location cap instead).
3. ~~Owner count~~ — **CONFIRMED 2026-06-25: single/≤3 owners is CS-only.** (Privately-held + no-PE/no-public still apply to both brands.)
4. The Clay table itself — cross-check it column-by-column so no threshold or check is missed (see "Referencing the old Clay table" below).

---

## Referencing the old Clay table — NO reconnect needed

The exported Clay CSVs in `data/clay-archive/{cs,fs}/` already preserve the **entire qualification pipeline** as columns. We can rebuild the exact logic from them — no live Clay access required (Clay's API gated table reads anyway, which is why we exported in the first place). Column → rule map, read from `cs/*Runs-Weekly*` (the richest, ~80 cols) + `Final-Results-Table`:

| Clay column(s) | Our rule |
|---|---|
| `Primary Industry`, `Size`, `Type` | #1 industry |
| `Ai: Find Revenue from Zoominfo URL` → `Company Revenue Results` → **`Revenue < $20M`** | #2 revenue *(⚠ Clay used **<$20M**; current rule per Theodore 2026-06-25 = **≤ $25M**)* |
| `Employee Count`, `Size` | #3 employees |
| `Ai: Franchise Status` → `Franchise Status Franchise Vs Private Results` | #8 brand (franchise vs private) |
| `Country` | #7 US business |
| `Founded`, `Founded Pre-2022` → `Operational Years` | #9 age ≥ 3yr |
| `Ai: Company Owner Name` → `Owner Name`, `Ai: Owner LinkedIn URL`, **`Employment_Status_Result`** | #10 current owner (still active) |
| `Ai: Owner US-Based` → `Owner US-Based ... Result` | #11 owner in US |
| `AI: Investigative Company Report` → `Company Research Results` | #5 ownership / PE / public (deep research) |
| `Lookup Block List Results`, `Block List Check`, `Instantly Lookup`, `Pipedrive Lookup` | suppression |
| `Qualified Status 2`, **`Qualified Lead Status (3 & Final)`** | the multi-stage qualified result |
| `Validate {LeadMagic,Icypeas,Findymail,Prospeo,DropContact,Datagma}` → `Master Work Email`, `US Email Check` | email find + verify waterfall |
| `Franchise - Add Lead to Campaign` / `Private - Add Lead to Campaign` | final ROUTE → FS vs CS campaign |

**Two takeaways:** (1) Clay ran qualification in **multiple stages** (`Qualified Status 2`, `... (3 & Final)`) — this validates our cheap→expensive funnel. (2) The only thing the CSV export does NOT carry is the exact **AI prompt text** behind the `Ai:`/`AI:` columns (Franchise Status, Owner US-Based, Investigative Report). We can write equivalent prompts, or — if you want them replicated verbatim — a **screenshot of those Clay column configs** is the easy way (not a live reconnect).

**⚠ Revenue discrepancy to confirm:** the Clay table gate was `Revenue < $20M`; Theodore stated **≤ $25M** on 2026-06-25. Using **$25M** as current/authoritative; flag if that's wrong.

---

## What already exists in code (so we extend, not rebuild)

- `models.Contact` carries `industry, sub_industry, company, company_size, company_founded, state, country, linkedin, title, full_name`.
- `verification.backfill_from_leadmagic()` already captures company industry/size/founded/LinkedIn during verify → Stage 1 is half-built.
- `scoring.py` has `EXCLUDED_VERTICALS`, `STRONG_VERTICALS`, `EXCLUDED_COMPANY_PATTERNS` (real-estate), owner-title detection.
- `audiences.SegmentSpec` filters: brand, tier, industry_contains, company_contains, states, min_icp.

**To build:** Stage-0 hard filters (country/geo), the AI qualification stage (#5/#8/#10/#11), the geo-radius targeter (#6), and the `qualification` result on Contact + a pre-send gate.
