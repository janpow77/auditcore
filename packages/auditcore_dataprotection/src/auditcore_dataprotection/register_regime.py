"""Regime- and role-specific register checks (profiles from 2026.10.4 on).

Each activity names its legal regime (``rechtsregime``) and the role of the
register-keeping body (``rolle``). The checks never pick a default: an
unclear regime or role is a blocking issue, a regime that differs from the
profile is a blocking issue, and § 65 HDSIG adds profiling and the legal basis
of every intended transfer as mandatory items. "Wenn möglich" fields (storage
period, TOM) accept either a concrete statement or a justification together
with the body that reviews it; the latter stays an open, non-blocking task.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

REGIME_GDPR = "dsgvo"
REGIME_HDSIG = "hdsig_ji"
REGIME_UNCLEAR = "unklar"
REGIMES = (REGIME_GDPR, REGIME_HDSIG, REGIME_UNCLEAR)

ROLE_CONTROLLER = "verantwortlicher"
ROLE_PROCESSOR = "auftragsverarbeiter"
ROLE_JOINT = "gemeinsam_verantwortlicher"
ROLES = (ROLE_CONTROLLER, ROLE_PROCESSOR, ROLE_JOINT)

#: Fields of the processor register (Art. 30 Abs. 2 DSGVO, § 65 Abs. 2 HDSIG).
PROCESSOR_REQUIRED = ("auftraggeber", "kategorien_verarbeitungen", "tom")
#: "Wenn möglich" fields: concrete value or justification plus reviewing body.
IF_POSSIBLE = ("speicherdauer", "tom")

#: ``issue(code, field, message, blocking=True)`` as in :mod:`.register_content`.
Report = Callable[..., None]


def _blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def activity_role(activity: Mapping[str, object]) -> str | None:
    """Declared role of the activity, ``None`` if missing or unknown."""
    role = activity.get("rolle")
    return role if isinstance(role, str) and role in ROLES else None


def check_regime(activity: Mapping[str, object], profile_regime: str, issue: Report) -> None:
    """Regime must be stated, known, clear and match the selected profile."""
    regime = activity.get("rechtsregime")
    if regime is None or regime == "":
        issue("missing_regime", "rechtsregime", "Rechtsregime der Tätigkeit ist nicht angegeben")
    elif regime not in REGIMES:
        issue("invalid_regime", "rechtsregime", f"Unbekanntes Rechtsregime „{regime}“")
    elif regime == REGIME_UNCLEAR:
        issue(
            "unclear_regime",
            "rechtsregime",
            "Rechtsregime ist ungeklärt; kein bestätigter Abschluss, bis es geprüft ist",
        )
    elif regime != profile_regime:
        issue(
            "regime_mismatch",
            "rechtsregime",
            f"Tätigkeit gehört zum Regime „{regime}“, das Profil gilt für „{profile_regime}“; "
            "die Tätigkeit ist im passenden Profil zu führen",
        )


def check_role(activity: Mapping[str, object], issue: Report) -> None:
    """The role decides the template; it is never inferred."""
    if activity.get("rolle") in (None, ""):
        issue("missing_role", "rolle", "Rolle (Verantwortlicher/Auftragsverarbeiter) fehlt")
    elif activity_role(activity) is None:
        issue("invalid_role", "rolle", f"Unbekannte Rolle „{activity.get('rolle')}“")


def check_profiling(activity: Mapping[str, object], issue: Report, *, mandatory: bool) -> None:
    """Profiling is always asked; under § 65 HDSIG an open answer blocks."""
    value = activity.get("profiling")
    if value is None:
        issue(
            "undecided_flag",
            "profiling",
            "Angabe zum Profiling fehlt",
            mandatory,
        )
    elif not isinstance(value, bool):
        issue("invalid_flag", "profiling", "Profiling muss mit Ja oder Nein angegeben werden")
    elif value and _blank(activity.get("profiling_beschreibung")):
        issue("missing_field", "profiling_beschreibung", "Beschreibung des Profilings fehlt")


def _transfer_entries(activity: Mapping[str, object]) -> Sequence[object]:
    entries = activity.get("uebermittlungen")
    return entries if isinstance(entries, list) else ()


def _check_transfer_entry(index: int, entry: object, issue: Report) -> None:
    where = f"uebermittlungen[{index}]"
    if not isinstance(entry, Mapping):
        issue("invalid_transfer", where, "Übermittlung muss Empfänger und Rechtsgrundlage nennen")
        return
    for key, title in (("empfaenger", "Empfänger"), ("rechtsgrundlage", "Rechtsgrundlage")):
        if _blank(entry.get(key)):
            issue("missing_field", f"{where}.{key}", f"{title} der Übermittlung fehlt")


def check_transfers(activity: Mapping[str, object], issue: Report) -> None:
    """Every intended transfer names recipient and legal basis (§ 65 Abs. 1 HDSIG)."""
    entries = _transfer_entries(activity)
    if activity.get("uebermittlung_extern") is False and not entries:
        return  # ausdrücklich keine Übermittlung an Stellen außerhalb der Dienststelle
    has_recipients = not _blank(activity.get("name_empfaenger")) or not _blank(
        activity.get("kategorien_empfaenger")
    )
    if has_recipients and not entries:
        issue(
            "missing_transfer_basis",
            "uebermittlungen",
            "Für die vorgesehenen Übermittlungen fehlt die Rechtsgrundlage je Empfänger",
        )
    for index, entry in enumerate(entries):
        _check_transfer_entry(index, entry, issue)


def check_if_possible(activity: Mapping[str, object], issue: Report) -> None:
    """Concrete value, or a justification with reviewing body (then an open task)."""
    for field in IF_POSSIBLE:
        if not _blank(activity.get(field)):
            continue
        reason = activity.get(f"{field}_begruendung")
        reviewer = activity.get(f"{field}_pruefstelle")
        if _blank(reason) or _blank(reviewer):
            issue(
                "missing_field",
                field,
                "Angabe fehlt; ohne konkrete Angabe sind Begründung und Prüfstelle zu nennen",
            )
        else:
            issue("open_justified", field, "Noch nicht konkretisiert (begründet)", False)


def check_processor(activity: Mapping[str, object], issue: Report) -> None:
    """Own template of the processor register, not a renamed controller form."""
    for field in PROCESSOR_REQUIRED:
        if _blank(activity.get(field)):
            issue(
                "missing_field", field, f"„{field}“ fehlt im Verzeichnis des Auftragsverarbeiters"
            )
    if activity.get("drittlandtransfer") is None:
        issue("undecided_flag", "drittlandtransfer", "Drittlandsübermittlung ist nicht angegeben")


#: Additional fields of profiles from 2026.10.4 on; type-checked for every profile.
EXTRA_TEXT = (
    "rechtsregime",
    "rolle",
    "profiling_beschreibung",
    "auftraggeber",
    "kategorien_verarbeitungen",
    "speicherdauer_begruendung",
    "speicherdauer_pruefstelle",
    "tom_begruendung",
    "tom_pruefstelle",
)
EXTRA_FLAGS = ("profiling",)


def extra_type_errors(activity: Mapping[str, object]) -> list[str]:
    """Type errors of the additional fields; the caller raises ``ValidationError``."""
    errors = [
        f"Feld '{name}' muss Text sein."
        for name in EXTRA_TEXT
        if activity.get(name) is not None and not isinstance(activity.get(name), str)
    ]
    errors.extend(
        f"Feld '{name}' muss Ja/Nein (True/False) oder leer sein."
        for name in EXTRA_FLAGS
        if activity.get(name) is not None and not isinstance(activity.get(name), bool)
    )
    transfers = activity.get("uebermittlungen")
    if transfers is not None and not isinstance(transfers, list):
        errors.append("Feld 'uebermittlungen' muss eine Liste sein.")
    return errors


def check_regime_activity(
    activity: Mapping[str, object], profile_regime: str, issue: Report
) -> bool:
    """All regime and role checks; returns True if the processor template applies."""
    check_regime(activity, profile_regime, issue)
    check_role(activity, issue)
    if activity_role(activity) == ROLE_PROCESSOR:
        check_processor(activity, issue)
        return True
    check_profiling(activity, issue, mandatory=profile_regime == REGIME_HDSIG)
    check_transfers(activity, issue)
    check_if_possible(activity, issue)
    return False


def item_text(value: object) -> str:
    """Readable text of a list entry, e.g. a transfer as "Empfänger – Rechtsgrundlage"."""
    if isinstance(value, Mapping):
        if "empfaenger" in value or "rechtsgrundlage" in value:
            recipient = str(value.get("empfaenger") or "?")
            return f"{recipient} – {value.get('rechtsgrundlage') or 'Rechtsgrundlage fehlt'}"
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    return str(value)
