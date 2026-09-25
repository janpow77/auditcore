"""Legacy RSS/publication-page normalization of auditdatabase ``rss.py`` (BaFin, CURIA, ECA)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any


def _legacy_entry_parts(entry: Mapping[str, Any]) -> tuple[str, str, str, Any]:
    title = entry.get("title", "Ohne Titel")
    link = entry.get("link", "")
    summary = entry.get("summary", entry.get("description", ""))
    published = entry.get("published", entry.get("updated", ""))
    return title, link, summary, published


def legacy_bafin_entry(entry: Mapping[str, Any], feed_name: str) -> dict[str, Any] | None:
    """``BaFinHarvester._normalize_entry``; ``hash()`` identities depend on PYTHONHASHSEED."""
    try:
        title, link, summary, published = _legacy_entry_parts(entry)
        entry_id = link.split("/")[-1] if link else str(hash(title))
        pub_date: Any = ""
        if published:
            try:
                parsed = entry.get("published_parsed")
                if parsed:
                    pub_date = datetime(*parsed[:6]).isoformat()
            except Exception:  # noqa: BLE001 - reproduces the bare except
                pub_date = published
        return {
            "id": f"bafin_{entry_id}",
            "title": title,
            "document_type": f"BaFin {feed_name.title()}",
            "source": "bafin",
            "source_url": link,
            "funding_period": "2021-2027",
            "fund": "EFRE",
            "published_date": pub_date,
            "metadata": {
                "feed": feed_name,
                "categories": [tag["term"] for tag in entry.get("tags", [])],
            },
            "content": f"{title}\n\n{summary}",
        }
    except Exception:  # noqa: BLE001
        return None


def legacy_curia_entry(entry: Mapping[str, Any], feed_name: str) -> dict[str, Any] | None:
    """``CURIAHarvester._normalize_entry`` (only ``C-`` cases; type ``Urteil`` never reached)."""

    try:
        title, link, summary, published = _legacy_entry_parts(entry)
        match = re.search(r"C-\d+/\d+", title + summary)
        case_number = match.group(0) if match else ""
        entry_id = (case_number or link.split("/")[-1]) if link else str(hash(title))
        return {
            "id": f"curia_{entry_id}",
            "title": title,
            "document_type": "Urteil" if feed_name == "urteile" else "Pressemitteilung",
            "source": "curia",
            "source_url": link,
            "funding_period": "2021-2027",
            "fund": "EFRE",
            "published_date": published,
            "metadata": {"feed": feed_name, "case_number": case_number},
            "content": f"{title}\n\n{summary}",
        }
    except Exception:  # noqa: BLE001
        return None


#: Placeholder "core reports" the source returned as successful documents when
#: no ECA page could be read. They are not real publications (LS-C13).
LEGACY_ECA_PLACEHOLDERS = (
    (
        "eca_sr_2024_cohesion",
        "Sonderbericht: Kohäsionspolitik 2021-2027 - Vereinfachung und Leistungsorientierung",
        "Sonderbericht",
        "ECA Sonderbericht zur Kohäsionspolitik der Förderperiode 2021-2027",
    ),
    (
        "eca_sr_2023_erdf",
        "Sonderbericht: EFRE-Förderung - Wirksamkeit und Wirtschaftlichkeit",
        "Sonderbericht",
        "ECA Sonderbericht zur EFRE-Förderung",
    ),
    (
        "eca_annual_2023",
        "Jahresbericht 2023 zum EU-Haushalt",
        "Jahresbericht",
        "Jahresbericht des Europäischen Rechnungshofs zum EU-Haushalt 2023",
    ),
)


def legacy_eca_core_reports() -> list[dict[str, Any]]:
    """``ECAHarvester._get_core_reports`` placeholders, marked as such only in this adapter."""
    return [
        {
            "id": identifier,
            "title": title,
            "document_type": kind,
            "source": "eca",
            "source_url": "https://www.eca.europa.eu/de/publications",
            "funding_period": "2021-2027",
            "fund": "EFRE",
            "content": content,
        }
        for identifier, title, kind, content in LEGACY_ECA_PLACEHOLDERS
    ]
