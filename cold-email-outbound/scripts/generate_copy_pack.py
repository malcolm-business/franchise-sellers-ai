"""Generate a human-readable copy-preview pack for review before go-live.

Renders every active stream's full sequence (subjects + all step bodies) against
real sample contacts, so Theodore can read and approve the actual emails.

Output: data/runtime/COPY-PREVIEW-PACK.html (styled, open in any browser) +
.md (gitignored — contain real names/companies). Script is committed + reproducible.

Run:  python3 cold-email-outbound/scripts/generate_copy_pack.py
"""
import sys
import html as _html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import config, data_layer, scoring, copy_gen
from engine.models import CampaignStream, STREAM_BRAND
from engine.pipeline import STREAM_TEMPLATE

# Active streams to preview (buyer_reactivation deferred — no cold source)
PREVIEW_STREAMS = [
    CampaignStream.SELLER_COLD_FS_NICHE,
    CampaignStream.SELLER_COLD_FS_BROAD,
    CampaignStream.SELLER_COLD_CS,
    CampaignStream.REFERRAL_PARTNER_ADVISOR,
    CampaignStream.EVENT_PRE,
    CampaignStream.EVENT_POST,
]

# Sample event vars for the event streams
EVENT_VARS = {"event_name": "the MUFC 2026 Conference", "event_location": "Las Vegas",
              "event_session": "Exit Planning breakout"}

SAMPLES_PER_STREAM = 3


def pick_samples(stream):
    """Pull a few real, ICP-eligible, non-excluded sample contacts for a stream."""
    if stream in (CampaignStream.REFERRAL_PARTNER_ADVISOR, CampaignStream.REFERRAL_PARTNER_ZOR):
        contacts = data_layer.load_contacts(config.TIER_C, limit=60)
        return contacts[:SAMPLES_PER_STREAM]
    brand = STREAM_BRAND[stream]
    contacts = data_layer.load_tier_a(brand, limit=400)
    scoring.apply_scores(contacts)
    eligible = [c for c in contacts
                if (c.icp_score or 0) >= config.ICP_THRESHOLD
                and not c.icp_breakdown.get("excluded_company")]
    # prefer contacts with a real company name for richer rendering
    eligible.sort(key=lambda c: (bool(c.company), c.icp_score or 0), reverse=True)
    return eligible[:SAMPLES_PER_STREAM]


def collect():
    """Build structured preview data: [{stream, brand, brand_name, steps_meta, subjects, samples:[...]}]."""
    data = []
    for stream in PREVIEW_STREAMS:
        brand = STREAM_BRAND[stream]
        tpl = copy_gen.parse_template(config.TEMPLATES_DIR / STREAM_TEMPLATE[stream])
        subjects = tpl["meta"].get("subjects", [])
        extra = EVENT_VARS if stream in (CampaignStream.EVENT_PRE, CampaignStream.EVENT_POST) else None
        samples = []
        for c in pick_samples(stream):
            steps = []
            for st in tpl["steps"]:
                body, meta = copy_gen.render(st["body"], c, brand=brand, extra_vars=extra)
                if st["n"] == 1 and subjects:
                    seed = c.canonical_id or c.email_norm or c.display_name
                    subj = copy_gen.slot_variables(
                        copy_gen.expand_spintax(subjects[copy_gen._stable_index(seed, len(subjects))], seed),
                        copy_gen.build_variables(c, brand, extra),
                    )
                else:
                    subj = ""
                steps.append({"n": st["n"], "delay": st["delay_days"], "subject": subj,
                              "body": body.rstrip(), "words": meta["word_count"]})
            samples.append({"name": c.display_name or "(no name)", "company": c.company or "(no company)",
                            "icp": c.icp_score, "industry": c.industry or "n/a", "steps": steps})
        data.append({"stream": stream.value, "brand": brand, "brand_name": config.BRANDS[brand]["name"],
                     "color": config.BRANDS[brand]["color"],
                     "n_steps": len(tpl["steps"]), "delays": [s["delay_days"] for s in tpl["steps"]],
                     "subjects": subjects, "samples": samples})
    return data


def render_md(data):
    out = ["# Cold Email — Copy Preview Pack", "",
           "Every active stream's full sequence, rendered against real sample contacts.",
           "Review + approve before go-live. Generated in dry-run (no sends).", "", "---", ""]
    for s in data:
        out.append(f"## {s['stream']}  ·  {s['brand']} ({s['brand_name']})")
        out.append(f"\n**Steps:** {s['n_steps']} · **Delays:** {s['delays']}\n")
        out.append("**Subject variants:**")
        for subj in s["subjects"]:
            out.append(f"- {subj}")
        out.append("")
        for i, c in enumerate(s["samples"], 1):
            out.append(f"### Sample {i}: {c['name']} — {c['company']}  (ICP {c['icp']}, {c['industry']})\n")
            for st in c["steps"]:
                hdr = f"**Step {st['n']}**" + (f" — subject: _{st['subject']}_" if st["subject"] else f" (delay {st['delay']}d)")
                out.append(f"{hdr} — {st['words']} words\n\n```\n{st['body']}\n```\n")
            out.append("---\n")
    return "\n".join(out)


def render_html(data):
    esc = _html.escape
    parts = ["""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cold Email · Copy Preview Pack</title>
<style>
  :root{--bg:#0f172a;--panel:#1e293b;--panel2:#273449;--border:#3b4861;--text:#e2e8f0;--dim:#94a3b8;--fs:#dc2626;--cs:#3b82f6;}
  *{box-sizing:border-box;} body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.5;}
  .wrap{max-width:920px;margin:0 auto;padding:32px 24px;}
  h1{font-size:26px;margin:0 0 6px;} .sub{color:var(--dim);font-size:14px;margin-bottom:24px;}
  .toc{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:14px 18px;margin-bottom:28px;font-size:14px;}
  .toc a{color:var(--text);text-decoration:none;margin-right:14px;white-space:nowrap;}
  .toc a:hover{text-decoration:underline;}
  .stream{margin-bottom:40px;border:1px solid var(--border);border-radius:10px;overflow:hidden;}
  .stream-hd{padding:14px 18px;font-weight:600;font-size:17px;color:#fff;}
  .stream-meta{padding:10px 18px;background:var(--panel);color:var(--dim);font-size:13px;border-bottom:1px solid var(--border);}
  .subjects{padding:10px 18px;background:var(--panel);font-size:13px;border-bottom:1px solid var(--border);}
  .subjects b{color:var(--text);} .subjects ul{margin:6px 0 0;padding-left:18px;} .subjects li{margin:2px 0;color:var(--dim);}
  .sample{padding:16px 18px;border-top:1px solid var(--border);}
  .sample-hd{font-weight:600;margin-bottom:4px;} .sample-sub{color:var(--dim);font-size:12px;margin-bottom:12px;}
  .step{margin:0 0 14px;}
  .step-hd{font-size:12px;color:var(--dim);margin-bottom:5px;text-transform:uppercase;letter-spacing:.04em;}
  .step-subj{color:var(--text);font-weight:600;text-transform:none;letter-spacing:0;}
  .email{background:#fff;color:#1a1a1a;border-radius:8px;padding:16px 18px;font-size:14px;white-space:pre-wrap;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;border:1px solid #cbd5e1;}
  .wc{color:var(--dim);font-size:11px;margin-top:4px;}
  .note{color:var(--dim);font-size:13px;margin:18px 0;}
  .explain{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:18px 20px;margin-bottom:24px;font-size:13.5px;}
  .explain-h{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--dim);margin:15px 0 6px;}
  .explain-h:first-child{margin-top:0;}
  .explain p{margin:0 0 4px;} .explain ul{margin:4px 0 0;padding-left:18px;} .explain li{margin:3px 0;color:var(--text);}
  .explain b{color:#fff;}
  .explain .fix{background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.32);color:#fcd34d;border-radius:8px;padding:11px 13px;margin-top:10px;line-height:1.55;}
</style></head><body><div class="wrap">
<h1>Cold Email · Copy Preview Pack</h1>
<div class="sub">Every active stream's full sequence, rendered live on real sample contacts. Generated in dry-run. Nothing has been sent.</div>

<div class="explain">
  <div class="explain-h">What this page is</div>
  <p>These are the <b>actual draft emails the system will send</b>, rendered live on real sample contacts from our list. This is not a record of past sends. The same templates render on a different real contact each time.</p>
  <div class="explain-h">What is real and automatic here</div>
  <ul>
    <li><b>Merge fields</b> (first name, company, industry) are filled in from each real contact.</li>
    <li><b>Subject lines rotate automatically</b> (spintax). Each contact gets one of the variants listed for the stream.</li>
    <li>The <b>offer line</b> and the <b>legal footer</b> (mailing address and opt-out) are added by the system, not typed into the template.</li>
    <li>When there is <b>no real personalization signal</b> for a contact, that line is removed rather than faked. So this preview is slightly leaner than the raw template, and that is intentional.</li>
  </ul>
  <div class="explain-h">Why it exists</div>
  <p>This is the <b>review and approve surface</b>. Read the exact emails as they will land here, instead of the raw template files. <b>Nothing sends until this copy is approved.</b></p>
  <div class="fix"><b>It is also where you catch what to fix.</b> Check each email against the copy guide and the Broker Copy Playbook: strip every em dash, sharpen the overused subjects, and replace the unprovable "sold for more than they expected" line with a credibility statement we can stand behind (27 years, confidentiality, our process). <b>Status: awaiting Malcolm's review.</b></div>
</div>

<div class="note"><b>Deferred:</b> buyer_reactivation (buyers live in the GHL CRM, no cold source).</div>
<div class="toc"><b>Jump to:</b> """]
    parts.append(" ".join(f'<a href="#{s["stream"]}">{esc(s["stream"])}</a>' for s in data))
    parts.append("</div>")

    for s in data:
        c_color = s["color"]
        parts.append(f'<div class="stream" id="{esc(s["stream"])}">')
        parts.append(f'<div class="stream-hd" style="background:{c_color}">{esc(s["stream"])} &middot; {esc(s["brand_name"])}</div>')
        parts.append(f'<div class="stream-meta">{s["n_steps"]} steps &middot; delays {s["delays"]} days &middot; brand {esc(s["brand"])}</div>')
        parts.append('<div class="subjects"><b>Subject variants (rotated):</b><ul>')
        for subj in s["subjects"]:
            parts.append(f"<li>{esc(subj)}</li>")
        parts.append("</ul></div>")
        for i, c in enumerate(s["samples"], 1):
            parts.append('<div class="sample">')
            parts.append(f'<div class="sample-hd">Sample {i}: {esc(c["name"])} &middot; {esc(c["company"])}</div>')
            parts.append(f'<div class="sample-sub">ICP score {c["icp"]} &middot; industry: {esc(str(c["industry"]))}</div>')
            for st in c["steps"]:
                if st["subject"]:
                    hd = f'Step {st["n"]} &nbsp; subject: <span class="step-subj">{esc(st["subject"])}</span>'
                else:
                    hd = f'Step {st["n"]} &nbsp; (sends {st["delay"]} days later)'
                parts.append(f'<div class="step"><div class="step-hd">{hd}</div>')
                parts.append(f'<div class="email">{esc(st["body"])}</div>')
                parts.append(f'<div class="wc">{st["words"]} words</div></div>')
            parts.append("</div>")
        parts.append("</div>")

    parts.append("</div></body></html>")
    return "\n".join(parts)


def main():
    data = collect()
    config.ensure_runtime_dir()
    md_path = config.RUNTIME_DIR / "COPY-PREVIEW-PACK.md"
    html_path = config.RUNTIME_DIR / "COPY-PREVIEW-PACK.html"
    md_path.write_text(render_md(data), encoding="utf-8")
    html_path.write_text(render_html(data), encoding="utf-8")
    print(f"Wrote {html_path}")
    print(f"Wrote {md_path}")
    print(f"Streams previewed: {len(data)}  ·  total samples: {sum(len(s['samples']) for s in data)}")


if __name__ == "__main__":
    main()
