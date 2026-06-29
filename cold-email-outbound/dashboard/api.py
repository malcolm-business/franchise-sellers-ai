"""Marketing Platform — operator API (FastAPI).

The interactive backend behind the /marketing dashboard. Lets Malcolm build,
preview, and save audiences and run campaign dry-runs from the browser — no code.

Endpoints (all under /api/marketing/, proxied by nginx with .htpasswd-internal auth):
  GET  /ping                      → {ok, mode}
  GET  /segments                  → saved segment specs
  POST /preview      {filters}    → fast sampled estimate (count + breakdown)
  POST /save         {name,...}   → save a segment spec
  POST /dryrun       {segment, sequence} → multi-channel dry-run funnel summary

Respects CEO_DRY_RUN: /dryrun never sends (orchestrator is dry-run-gated). Mutating
endpoints only write segment specs (no external calls).

Run locally:  uvicorn dashboard.api:app --port 8083
Deployed as a systemd service on the droplet (see deploy/marketing-api.service).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from engine import config, audiences, orchestrator
from engine.audiences import SegmentSpec
from engine.sequences import DEFAULT_SEQUENCES

app = FastAPI(title="Marketing Platform Operator API", version="1.0")


class Filters(BaseModel):
    name: str = "preview"
    brand: str = ""
    tier: str = "A"
    industry_contains: list[str] = []
    company_contains: list[str] = []
    states: list[str] = []
    min_icp: int = 0
    require_email: bool = True
    require_linkedin: bool = False
    limit: int | None = None


class DryRunReq(BaseModel):
    segment: str                 # saved segment name
    sequence: str                # sequence name
    campaign_name: str = "dashboard dry-run"


def _spec(f: Filters) -> SegmentSpec:
    return SegmentSpec(
        name=f.name, brand=f.brand, tier=f.tier,
        industry_contains=f.industry_contains, company_contains=f.company_contains,
        states=f.states, min_icp=f.min_icp, require_email=f.require_email,
        require_linkedin=f.require_linkedin, limit=f.limit,
    )


@app.get("/api/marketing/ping")
def ping():
    return {"ok": True, "mode": "DRY-RUN" if config.DRY_RUN else "LIVE"}


@app.get("/api/marketing/segments")
def list_segments():
    out = []
    for name in audiences.list_segments():
        spec = audiences.load_segment(name)
        if spec:
            out.append(spec.to_dict())
    return {"segments": out}


@app.get("/api/marketing/sequences")
def list_sequences():
    return {"sequences": [{"name": n, "brand": s.brand, "n_touches": len(s.touches),
                           "channels": sorted(s.channels_used())} for n, s in DEFAULT_SEQUENCES.items()]}


@app.post("/api/marketing/preview")
def preview(f: Filters):
    try:
        return audiences.preview_sampled(_spec(f))
    except Exception as e:
        raise HTTPException(500, f"preview failed: {e}")


@app.post("/api/marketing/save")
def save(f: Filters):
    if not f.name or f.name == "preview":
        raise HTTPException(400, "give the segment a name")
    spec = _spec(f)
    path = audiences.save_segment(spec)
    return {"saved": f.name, "path": str(path)}


@app.post("/api/marketing/dryrun")
def dryrun(req: DryRunReq):
    if req.sequence not in DEFAULT_SEQUENCES:
        raise HTTPException(400, f"unknown sequence: {req.sequence}")
    spec = audiences.load_segment(req.segment)
    if not spec:
        raise HTTPException(404, f"segment not found: {req.segment}")
    try:
        # Cap the simulation to a representative sample so the API responds fast.
        sample_contacts = audiences.build_segment_capped(spec, cap=600)
        summary = orchestrator.run_multichannel_campaign(
            campaign_name=req.campaign_name, audience=sample_contacts,
            sequence_name=req.sequence, do_verify=True)
        d = summary.to_dict()
        d["simulation_note"] = f"projected from a {len(sample_contacts)}-contact sample of '{req.segment}'"
        return d
    except Exception as e:
        raise HTTPException(500, f"dry-run failed: {e}")


@app.get("/api/marketing/health")
def health():
    return JSONResponse({"ok": True, "mode": "DRY-RUN" if config.DRY_RUN else "LIVE",
                         "segments": len(audiences.list_segments()),
                         "sequences": len(DEFAULT_SEQUENCES)})
