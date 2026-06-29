"""Channel implementations for the multi-channel marketing platform.

Each channel implements BaseChannel so the orchestrator can dispatch a Touch to
any channel through one interface. Add a new channel = add a module here + register.

    email     -> Instantly        (live-tested)
    linkedin  -> HeyReach         (dry-run gated; needs HEYREACH_API_KEY)
    ads       -> Google + Meta    (interface ready; needs ad API access)
    postcard  -> Lob/PostGrid     (stub for later)
"""
from .base import BaseChannel, get_channel, CHANNEL_REGISTRY  # noqa: F401
from . import email_channel, linkedin_channel, ads_channel, postcard_channel  # noqa: F401
