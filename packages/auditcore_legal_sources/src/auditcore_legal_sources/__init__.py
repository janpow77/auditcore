"""Legal and audit publication sources (Bundestag DIP, EUR-Lex, BaFin, CURIA, ECA).

Parsers and normalization are pure; :mod:`auditcore_legal_sources.adapters`
connects them to the shared ``auditcore_harvest`` engine.
"""

from .errors import ConfigurationError, LegalSourceError, ParseError, ProfileError
from .model import LegalDocument
from .profile import SourceProfile, available_profiles, load_profile

__version__ = "0.1.4"

__all__ = [
    "ConfigurationError",
    "LegalDocument",
    "LegalSourceError",
    "ParseError",
    "ProfileError",
    "SourceProfile",
    "__version__",
    "available_profiles",
    "load_profile",
]
