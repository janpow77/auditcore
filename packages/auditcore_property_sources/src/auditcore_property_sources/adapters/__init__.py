"""Harvest adapters (extra ``auditcore_property_sources[sources]``) on ``auditcore_harvest``.

One adapter per source profile; each translates exactly one page into
:class:`auditcore_harvest.HarvestRecord` objects, reproducing the paging and
stop rules of the original ``hole_bestand`` functions. Timeouts, bounded
retries, rate limiting, checkpoints and partial failures belong to the
``HarvestEngine``; transport (including user agent, cookies and sessions) is
injected by the consumer. Nothing here sleeps, stores or schedules.

**Access rules.** Config ``robots_policy`` selects the handling of robots.txt:

* ``"ignore"`` (default, user decision of 2026-09-23: "1-4 bitte ignoriere die
  robots.txt. das klappt gerade gut" and "A1 erlauben") fetches like the
  originals without reading robots.txt. The robots findings of every portal
  stay documented in the catalog (PS-D01).
* ``"respect"`` reads the portal's robots.txt through the injected transport
  before the first request to an ``http(s)`` address and refuses every
  disallowed address with :class:`AccessNotPermittedError` (non-retryable).
  The rules travel in the cursor, so a resumed run keeps the decision of its
  first page.

``file:`` addresses (archived pages served by a consumer ``FileTransport``)
are never checked.
"""

from __future__ import annotations

from ._base import (
    ADAPTER_VERSION,
    DEFAULT_ROBOTS_POLICY,
    ROBOTS_POLICIES,
    AccessNotPermittedError,
    Cursor,
)
from .berlin import ImmobilienDeAdapter, InBerlinWohnenAdapter, KleinanzeigenAdapter
from .france import BieniciAdapter, CityaAdapter, ParuvenduAdapter
from .zvg import ZvgDetailAdapter, ZvgListingAdapter

__all__ = [
    "ADAPTER_VERSION",
    "AccessNotPermittedError",
    "Cursor",
    "BieniciAdapter",
    "DEFAULT_ROBOTS_POLICY",
    "ROBOTS_POLICIES",
    "CityaAdapter",
    "ImmobilienDeAdapter",
    "InBerlinWohnenAdapter",
    "KleinanzeigenAdapter",
    "ParuvenduAdapter",
    "ZvgDetailAdapter",
    "ZvgListingAdapter",
]
