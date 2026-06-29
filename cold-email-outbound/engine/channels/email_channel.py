"""Email channel — wraps the existing Instantly sending + copy_gen.

This adapts the already-built, live-tested email layer to the BaseChannel
interface so it plugs into the multi-channel orchestrator alongside the others.
"""
from __future__ import annotations

from .. import config, copy_gen, sending
from ..models import Contact, CampaignStream
from ..sequences import Touch
from .base import BaseChannel, register


class EmailChannel(BaseChannel):
    name = "email"

    def is_available(self) -> bool:
        return bool(config.get_key(config.INSTANTLY["key_env"]))

    def can_reach(self, contact: Contact) -> bool:
        return bool(contact.email_norm)

    def execute_touch(self, contact: Contact, touch: Touch, campaign: dict) -> dict:
        """Render + (dry-run) queue one email step for this contact."""
        brand = campaign.get("brand", "CS")
        tpl_path = config.TEMPLATES_DIR / touch.template
        if not tpl_path.exists():
            return {"channel": self.name, "ok": False, "error": f"template not found: {touch.template}"}
        tpl = copy_gen.parse_template(tpl_path)
        # touch.step indexes into the email sequence; map to the right template step
        # (templates have their own 1..n steps; we use the matching one or step 1)
        steps = {s["n"]: s for s in tpl["steps"]}
        # email touches in a sequence may not line up 1:1 with template steps; use params override
        tstep = touch.params.get("template_step", _email_step_ordinal(campaign, touch))
        step = steps.get(tstep, tpl["steps"][0])
        body, meta = copy_gen.render(step["body"], contact, brand=brand,
                                     test_offer=campaign.get("test_offer"),
                                     extra_vars=campaign.get("extra_vars"))
        if config.DRY_RUN:
            from .. import data_layer
            data_layer.log_dry_run("channel:email",
                                   f"WOULD send email step to {contact.email_original}",
                                   {"canonical_id": contact.canonical_id, "template": touch.template,
                                    "words": meta["word_count"]})
            return {"channel": self.name, "ok": True, "dry_run": True, "rendered_words": meta["word_count"]}
        # Live path delegates to the existing sending layer (campaign already created upstream)
        return {"channel": self.name, "ok": True, "dry_run": False,
                "note": "live email send handled by sending.push_leads at campaign level"}


def _email_step_ordinal(campaign: dict, touch: Touch) -> int:
    """Map this email touch to a template step number (1-based among email touches)."""
    return campaign.get("_email_step_counter", {}).get(touch.step, 1)


register(EmailChannel())
