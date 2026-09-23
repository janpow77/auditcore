"""Property source profiles: rental portals and forced-auction notices, kept separate.

Each module is one characterized source profile with its own price, area and
address semantics; nothing is harmonised across portals:

* :mod:`.immobilien_de`, :mod:`.inberlinwohnen`, :mod:`.kleinanzeigen` —
  Berlin rental offers (wohnungsmonitor, profile "berlin");
* :mod:`.bienici`, :mod:`.citya`, :mod:`.paruvendu` — French rental offers
  (wohnungsmonitor, profile "frankreich");
* :mod:`.zvg` and :mod:`.zvg_lifecycle` — forced-auction notices and their
  status lifecycle (versteigerung).

The parsers use only the standard library. Harvest adapters are in
:mod:`.adapters` (extra ``sources``, depends on ``auditcore_harvest``). The
access status of every portal (robots.txt, terms of use) is in
:func:`catalog`. See README.md and docs/behavior-changes.md.
"""

from .catalog import catalog, source_entry
from .errors import AccessNotPermitted, DependencyError, PropertySourceError
from .robots import RobotsRules, is_allowed, parse_robots

__version__ = "0.1.0"

__all__ = [
    "AccessNotPermitted",
    "DependencyError",
    "PropertySourceError",
    "RobotsRules",
    "__version__",
    "catalog",
    "is_allowed",
    "parse_robots",
    "source_entry",
]
