"""Profile: gebündelte, versionierte Kataloge je Förderperiode.

Mitgeliefert: ``foerderperiode-2021-2027`` (KA nach Anhang XI VO (EU)
2021/1060) und ``foerderperiode-2014-2020`` (KA nach Anhang IV Delegierte
VO (EU) Nr. 480/2014), erzeugt mit ``tools/build_profiles.py`` aus den
amtlichen Texten. Bewertungskriterien enthält keiner der beiden
Rechtstexte; die Anwendung speist sie über
:meth:`Profile.with_assessment_criteria` ein.
"""

from .loader import (
    PROFILE_SCHEMA,
    STANDARD_PROFILE,
    ProfileRegistry,
    available_profiles,
    load_profile,
    load_template,
    profile_from_dict,
)
from .model import (
    AssessmentCriterion,
    KeyRequirement,
    LegalBasisTemplate,
    Profile,
    SegregationRule,
    Selection,
    Template,
)

__all__ = [
    "PROFILE_SCHEMA",
    "STANDARD_PROFILE",
    "AssessmentCriterion",
    "KeyRequirement",
    "LegalBasisTemplate",
    "Profile",
    "ProfileRegistry",
    "SegregationRule",
    "Selection",
    "Template",
    "available_profiles",
    "load_profile",
    "load_template",
    "profile_from_dict",
]
