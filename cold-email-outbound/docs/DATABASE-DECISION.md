# Database Decision — Cold Email System

**For:** Theodore · **Prepared:** 2026-06-27 · **Status:** decision needed
**One-line recommendation:** **Move to Neon (managed cloud Postgres).** Free to start, ~$19/mo as it grows, off your laptop, real SQL with no row limits, I run it entirely for you, and it has managed backups. The $0 alternative is hosting Postgres/SQLite on the droplet we already pay for. RevyOps is not worth it for us.

Read sections 1–3 for the decision; 4–6 are the detail.

---

## 1. The decision in plain terms

Right now the entire 187K-contact pool and all campaign history live as **flat CSV/JSONL files on your laptop**. That was fine for building. It is not fine for running a real operation, for three reasons you already named:

- It's **on your laptop** (single machine, no backup, not accessible to the engine when it runs on the droplet).
- It **can't be queried** well ("how many CS leads in cooldown right now?" means loading a 190MB file every time).
- It **won't scale** cleanly once we add qualification results, send/reply history, and weekly analytics across many campaigns.

So we move the data to a proper cloud database. The only real question is **which one**. Your constraints were clear: off the laptop, cloud, queryable, no row limits (Airtable failed you here), not scattered across tables (Clay failed you here), cheap, and **runnable by me without your team ever logging in**.

The good news: this is a **swappable, low-risk change**. The engine was deliberately built so that one file (`engine/data_layer.py`) is the *only* place that touches storage. Switching databases means rewriting that one file. Nothing else in the system changes.

---

## 2. What the database actually has to do

So the comparison is concrete, here is the real workload:

- **Hold the canonical pool** — ~405K total people (187K sendable Tier A + 155K re-verify + referral + suppression), each a wide record (name, company, title, industry, location, LinkedIn, verification status, qualification result, source, suppression flags).
- **Grow with activity** — every send, reply, bounce, unsubscribe, and reply-classification becomes a row. Over a year of sending this is easily millions of small rows.
- **Answer live questions** — who's qualified, who's in cooldown, what bounced this week, which segment/offer is winning, who's already in the CRM. These are SQL queries, not file scans.
- **Be the single source of truth** — replace the scattered CSVs with one place I read and write, so dedup and "skip already-contacted" are trivial.
- **Be operated by me** — the team never logs into it. I read/write via API or command line.

This shape — relational, growing, query-heavy — points at **Postgres** (or SQLite at our current scale). It does not point at a spreadsheet (Airtable) or a no-code table tool (Clay), which is exactly why both frustrated you.

---

## 3. The options, scored against your criteria

| Option | Monthly cost | Off your laptop | Queryable, no limits | I run it (no team login) | Managed backups | Bottom line |
|---|---|---|---|---|---|---|
| **Neon** (managed Postgres) | **$0 → ~$19/mo** | ✅ | ✅ real SQL | ✅ API + CLI | ✅ automatic | **Recommended.** Cheapest managed Postgres, scales to zero when idle, nothing for you to maintain. |
| **Droplet-hosted** (Postgres or SQLite on our server) | **$0** (already paid) | ✅ | ✅ | ✅ | ⚠️ I set up backups | Best if you want zero new recurring cost; co-located with the engine. |
| **Supabase** (managed Postgres) | $0 → $25/mo | ✅ | ✅ | ✅ | ✅ | Fine, but $25/mo bundles auth/file-storage/realtime we don't need. |
| **Turso** (cloud SQLite) | $0 (generous free) | ✅ | ✅ | ✅ | ✅ | Good free tier, but SQLite semantics; Postgres is more future-proof for analytics. |
| **RevyOps** | **$229/mo Growth · $499/mo Scale** (billed per event) | ✅ | ✅ + dashboards | partial (it's a UI product) | ✅ | **Not recommended for us** — see section 5. |
| **Keep flat files** (just move them to the droplet) | $0 | ✅ if on droplet | ❌ weak | ✅ | ⚠️ | Cheapest stopgap; breaks the moment we want real analytics. |

**My recommendation: Neon.** It is the cleanest fit for every one of your constraints, it's the cheapest *managed* option, and "managed" matters here because this database holds the asset (the contact pool) — losing it would be catastrophic, and Neon backs it up automatically so I never have to think about it and neither do you.

**The honest $0 alternative: host it on our droplet.** We already pay for the DigitalOcean droplet that runs the dashboards. Putting Postgres (or the even-lighter SQLite) there costs nothing extra and keeps the data in our own infrastructure, co-located with the engine. The one tradeoff is that *I* own the backups rather than the provider — manageable (I'd set a nightly backup to DigitalOcean storage), but it's real work and a single server is a single point of failure.

If your instinct is "spend nothing," we host on the droplet. If your instinct is "spend a little to never worry about losing the data," we use Neon. Either way I do all the work.

---

## 4. Why Neon over the other paid managed options

- **vs Supabase:** Supabase is also good, but its value is the *bundle* (database + auth + file storage + realtime). We need only the database. Supabase Pro is $25/mo and runs compute 24/7; Neon is ~$19/mo, **scales to zero when idle** (we send in bursts, so the DB sits idle a lot — we'd pay for almost none of it), and the free tier likely covers our first months outright. For a database-only need, Neon is the better value.
- **vs Turso:** Turso's free tier is generous and it's genuinely good, but it's cloud **SQLite**. SQLite is excellent for a single writer; Postgres handles concurrent campaigns and heavier analytical queries more comfortably as we scale. Since the price difference is negligible, I'd rather start on Postgres and never have to migrate again.
- **Cost reality at our size:** ~405K contacts + growing event logs is roughly 1–2 GB at maturity. Neon's free tier is 0.5 GB, so we'd move to the **Launch plan (~$19/mo)** within a few months. That is still the cheapest managed Postgres on the market, and **~12–26× cheaper than RevyOps** ($229–499/mo).

---

## 5. Why not RevyOps (even though Ben's tool is impressive)

RevyOps is genuinely well-built and Ben knows this space. But it's the wrong buy **for us specifically**:

- **It's a platform, not a database.** You pay **$229/mo (Growth) or $499/mo (Scale)** for a Client Data Platform — centralized dashboards, dedup, GTM reporting. Those are real features. The problem: **we have already built those ourselves.** Our `/marketing` operator dashboard, the dedup pipeline (1.3M → 187K), the suppression/CRM-sync, and the analytics layer are done. RevyOps would have us pay monthly for capability we own.
- **Per-event billing punishes the volume we want.** RevyOps charges by *event* — and our system generates huge event counts (every send, reply, bounce, enrichment). The bill rises exactly as we scale sending. Neon bills on storage + compute (cheap, roughly flat). For a high-volume sender, Neon's cost model is structurally better.
- **It's another login + another vendor.** Your goal is fewer tools the team touches and lower cost per lead. RevyOps adds a vendor and a recurring bill to do a job a $0–19/mo database does for us, with me operating it.

### 5a. Feature-by-feature: is there anything in RevyOps we *can't* do?
**No — we've already built the equivalent of nearly their entire list.** Multi-source list building, enrich/clean, contact+company DB, historical logs, advanced search, open API + MCP → our dedup + LeadMagic + **Neon SQL** + Neon's MCP. Cold-email/LinkedIn/deliverability dashboards → our `/marketing` dashboard + the planned health monitor. Central DNC + cross-channel sync → our 3-layer suppression + orchestrator. Saved views/segmentation, automated triggers, A/B copy → audience builder + offer rotation + crons + the A/B skill. Unified person graph, CRM integration, lead scoring → our `canonical_id` dedup + direct GHL FS/CS + ICP scoring. The only two things RevyOps offers that are genuinely *different* (not capabilities we lack): (1) a **vendor-maintained turnkey product + UI**, and (2) **automatic ongoing dedup on ingest**. We replicate (2) with the same dedup logic we already wrote; (1) is convenience we trade for control + ~$0–19/mo.

### 5b. Long-term risks of Neon (honest)
**Real:** (a) **maintenance + bus-factor** — more of the system is our code that I run, vs a vendor product (mitigated: most is already built, Malcolm operates a *dashboard UI* not SQL, plus runbooks); (b) we must **build ingest-dedup** for net-new sources (planned, low effort). **Not real:** lock-in (standard Postgres — `pg_dump` and move anytime; the opposite of RevyOps' proprietary platform), longevity (Neon is Databricks-owned, ~$1B), scale-to-zero cold starts (negligible for batch use), storage cost (single-digit $/mo for years; archive old events), PII-in-cloud (same as RevyOps, but we control region/access — or use the droplet to keep it fully in-house).
- **Lock-in.** Our pool would live in their platform. With Neon or the droplet, the data is plain Postgres we fully control and can move anytime.

If we did *not* already have the dashboard + dedup + engine built, RevyOps would be a reasonable shortcut. Because we do, it's paying twice.

---

## 6. What happens after you decide (the migration)

This is low-risk and I do all of it:

1. You pick **Neon** (I'll set up the free project and share nothing you need to manage) or **droplet** (I stand up Postgres/SQLite on our server).
2. I rewrite the single storage module (`engine/data_layer.py`) to read/write the new database. **No other code changes** — the engine was built for exactly this swap.
3. I load the 187K pool + all campaign history into it and run a **parity check** (row counts + a sample of records must match the old CSVs exactly — zero data loss, same contract we used for the original dedup).
4. The flat files become a backup snapshot; the database becomes the source of truth.
5. From then on, qualification results, send/reply history, and the weekly analytics all live in one queryable place I operate for you.

**Timeline:** about half a day of work once you decide. It does not block the other work — I can build the qualification layer in parallel and point it at whichever store you choose.

---

## 7. What I need from you

Just the direction:

- **Neon (recommended):** say the word and I set up the free project today; we move to the ~$19/mo plan only when the data outgrows the free tier (a few months out).
- **Droplet ($0):** say the word and I stand it up on our existing server; I'll also set up a nightly backup so a single-server failure can't lose the pool.

Either choice satisfies everything you asked for: off your laptop, cloud, queryable, no limits, cheap, and run entirely by me. My vote is **Neon** for the managed backups on an irreplaceable asset, with **droplet** as the equally-fine $0 path if you'd rather not add any recurring cost.
