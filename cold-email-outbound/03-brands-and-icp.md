# Brands and ICP

Two related-but-distinct brands, one engine. Same offer (free Opinion of Value, with a portfolio of alternatives in `04-offer-concepts.md`), distinct personas. Brand separation enforced at the sending domain layer; everything else is shared.

---

## Franchise Sellers

**Audience:** Franchisee owners — operators who own one or more units of a franchise system.

**Sending domains:** ~30 warmed domains tagged for this brand inside Instantly.

**CRM:** GoHighLevel workspace dedicated to Franchise Sellers (configured by Deal Studio).

### ICP — who we want to reach

The owners most likely to be open to an exit conversation share several characteristics. None of these are required individually; the more that stack on a single record, the higher the targeting score.

| Signal | Why it matters |
|--------|----------------|
| Tenure in the franchise system: 10+ years | Long-tenured franchisees are statistically more likely to be considering exits than newer owners |
| Multi-unit ownership (2+ units) | Higher deal value, more sophisticated owners, more legitimate exit candidates |
| Owner age: 55+ | Demographic correlation with exit-readiness |
| Recent operational transitions | Promoting a manager to GM, family member joining or leaving the business — owners often start exit thinking around these moments |
| Franchise system M&A activity | When the franchisor or other franchisees in the system get acquired, every other franchisee notices |
| Geographic concentration | Owners in regions with active M&A in their vertical are more receptive |
| LinkedIn bio language signals | "Transitioning," "advising," "exploring next chapter," "pursuing other interests" |

### Sourcing notes

LinkedIn Sales Navigator is the richest source for tenure and personnel signals on franchisees. Franchise Disclosure Documents (FDDs) reveal system-level health. Specific franchise industry publications (Franchise Times, Franchise Business Review) sometimes publish system-level transition data. State franchise registrations are a public-record source for active franchisees in California, New York, Illinois, and a handful of other registration states.

### Persona-specific copy notes

Franchisees identify with their *system* (the brand) more than independent owners identify with their *industry*. Reference the franchise system by name when possible. The fact that you specialize in their franchise system is itself credibility ("I work with [System] franchisees specifically"). Multi-unit owners think in terms of *portfolio* — frame conversations around their portfolio of units, not just "your business."

---

## Company Sellers

**Audience:** Independent business owners — operators who own a non-franchised business.

**Sending domains:** ~30 warmed domains tagged for this brand inside Instantly.

**CRM:** GoHighLevel workspace dedicated to Company Sellers (configured by Deal Studio).

### ICP — who we want to reach

| Signal | Why it matters |
|--------|----------------|
| Years in business: 10+ | Owners hit exit-eligible age range; business has had time to mature |
| Owner age: 55+ | Demographic correlation with exit |
| Revenue range: $1M–$25M (refine based on actual conversion data) | Below this, deal economics get hard; above this, larger M&A advisors crowd the space |
| Industry consolidation activity | When peers are getting bought, owners notice |
| Recent leadership changes | Bringing on a GM, changing CFOs, divesting partners |
| Lifestyle signals on LinkedIn | "Transitioning," "advisor," "pursuing other interests," "succession," step-back language |
| Local M&A activity in their vertical | When a comparable business sells in the same metro, every other owner suddenly cares about their valuation |
| Industry — strong verticals | Businesses where M&A is already active: HVAC, home services, manufacturing, distribution, professional services, niche B2B |

### Sourcing notes

PDL is strongest for owner-age and tenure data. Apollo for firmographic filtering. Crunchbase for funding and corporate transaction signals (limited use for SMB but useful for the upper end). LinkedIn Sales Navigator for personnel and bio signals. Local business journals (American City Business Journals network) regularly publish "Business of the Year"/"Largest Private Companies" lists that are good lead sources.

### Persona-specific copy notes

Independent owners identify with their *industry* and the *business they built*, not a system. Reference what they *do* and how long they've been doing it. Mention specific operational details when possible — these owners pride themselves on knowing every detail of their business. The opening signal often works best when it's about the business itself, not the owner's online presence.

---

## Shared ICP scoring framework

Both brands score records against a 0–100 ICP fit scale, computed by Claude Code at the moment of sourcing/enrichment. Records below a threshold (suggested starting point: 60) don't get sequenced. The scoring weights signals from the tables above:

- Demographic + tenure signals: ~40%
- Behavioral / situational signals (transitions, M&A activity, bio language): ~40%
- Firmographic match (industry, size, geography): ~20%

We refine the weights once we have real reply-rate data per signal. The framework above is a v1 starting point.
