"""Cold Email Engine.

A Claude Code-orchestrated outbound email engine for Franchise Sellers + Company
Sellers. Built dry-run-first: every external-API touchpoint is gated by
config.DRY_RUN, so the full system runs end-to-end against real data without
sending, verifying, or spending a credit until you flip the switch.

Module map:
    config       - central config + DRY_RUN master switch
    models       - Contact, CampaignStream, ReplyCategory, SendStatus, SendEvent
    data_layer   - flat-file read/write (Phase 1 source of truth = dedup output)
    scoring      - ICP 0-100 scoring
    suppression  - Layer A pre-send filter
    copy_gen     - spintax + signal-anchor + offer rotation
    verification - LeadMagic -> ZeroBounce waterfall (dry-run gated)
    sending      - Instantly push (dry-run gated)
    engagement   - webhook/poll -> event log (dry-run gated)
    classify     - reply classification via Claude API (dry-run = heuristic)
    routing      - CRM routing to GHL / Buyer Manager / nurture (dry-run gated)
    pipeline     - end-to-end orchestrator
    selftest     - runs everything in dry-run against real Tier A data
"""

__version__ = "0.1.0-dryrun"
