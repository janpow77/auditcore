"""TED company search (mnemonic fields) and HAD (Hessische Ausschreibungsdatenbank).

Two characterized source variants each, kept separate and never merged:

* ``flowinvoice`` — ``janpow77/flowinvoice@fb2d185`` ``company_records.py``
  (TED ``GET /api/v3.0``, HAD ``onlinesuche_suche.html``);
* ``designer`` — ``janpow77/audit_designer@030a71e`` ``company_records.py``
  (TED ``POST /v3``, alpha-3 countries, multilingual title; HAD
  ``onlinesuche_erweitert.html``, HTTP 404 = no hit).

``legacy_*`` functions reproduce the source exactly, including that every
error (HTTP status, invalid JSON, parser exception) silently returns an empty
list. The corrected contract (:func:`ted_company_result`, :func:`had_result`)
returns an explicit :class:`SearchResult` so an incomplete call never looks
like "no hits". Network access is not performed here; adapters built on
``auditcore_harvest`` send the request descriptions and pass the responses in.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .records import COVERAGE_TENDER_SEARCH

VARIANTS = ("flowinvoice", "designer")
TED_SEARCH_URL = {
    "flowinvoice": "https://ted.europa.eu/api/v3.0/notices/search",
    "designer": "https://api.ted.europa.eu/v3/notices/search",
}
HAD_SEARCH_URL = {
    "flowinvoice": "https://www.had.de/onlinesuche_suche.html",
    "designer": "https://www.had.de/onlinesuche_erweitert.html",
}
DESIGNER_COUNTRY_MAP = {
    "DE": "DEU",
    "AT": "AUT",
    "FR": "FRA",
    "IT": "ITA",
    "ES": "ESP",
    "PL": "POL",
    "NL": "NLD",
    "BE": "BEL",
}
TED_NOTICE_FIELDS = (
    "publication_number",
    "publication_date",
    "notice_title",
    "buyer_name",
    "buyer_country",
    "contract_type",
    "procedure_type",
    "cpv_code",
    "estimated_value",
    "currency",
    "winner_name",
    "award_date",
    "final_value",
    "notice_type",
    "url",
)
HAD_NOTICE_FIELDS = (
    "titel",
    "vergabestelle",
    "vergabeart",
    "leistungsart",
    "cpv",
    "ort",
    "frist",
    "bekanntmachung_id",
    "url",
    "datum",
)

STATUS_OK = "ok"
STATUS_NO_HIT = "no_hit"
STATUS_RATE_LIMITED = "rate_limited"
STATUS_FAILED = "failed"


@dataclass(frozen=True)
class SearchResult:
    """Explicit outcome of one company search; ``notices`` is complete only if ``ok``."""

    status: str
    notices: tuple[Mapping[str, str], ...] = ()
    error: str = ""
    coverage: str = COVERAGE_TENDER_SEARCH
    variant: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def complete(self) -> bool:
        """True for ``ok`` and ``no_hit``: the source answered the whole query."""
        return self.status in (STATUS_OK, STATUS_NO_HIT)


def _check_variant(variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"Unbekannte Quellvariante '{variant}'. Zulässig: {', '.join(VARIANTS)}.")


def _ted_notice(**values: Any) -> dict[str, Any]:
    notice: dict[str, Any] = dict.fromkeys(TED_NOTICE_FIELDS, "")
    notice["currency"] = "EUR"
    notice.update(values)
    return notice


# ------------------------------------------------------------------- TED


def ted_company_request(company_name: str, country: str, variant: str) -> dict[str, Any]:
    """Request description of the variant (method, URL, parameters/body, headers, timeout)."""
    _check_variant(variant)
    escaped = company_name.replace('"', "")
    if variant == "flowinvoice":
        return {
            "method": "GET",
            "url": TED_SEARCH_URL[variant],
            "params": {
                "query": f'FT="{escaped}" AND CY={country}',
                "fields": "ND,PD,TI,OL,NC,PR,TV",
                "pageSize": 50,
                "pageNum": 1,
                "scope": 3,
            },
            "headers": {"Accept": "application/json", "User-Agent": "EFRE-AuditTool/2.0"},
            "timeout": 30,
        }
    cy = DESIGNER_COUNTRY_MAP.get(country.upper(), country.upper())
    return {
        "method": "POST",
        "url": TED_SEARCH_URL[variant],
        "json": {
            "query": f'FT="{escaped}" AND CY={cy}',
            "fields": ["ND", "PD", "TI", "OL", "NC", "PR", "TV"],
        },
        "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        "timeout": 30,
    }


def _designer_title(value: Any) -> str:
    if isinstance(value, str):
        return value[:200]
    if isinstance(value, dict):
        title: Any = value.get("deu", "") or value.get("eng", "") or next(iter(value.values()), "")
        return title[:200]  # type: ignore[no-any-return]
    return ""


def _ted_items(payload: Any, variant: str) -> list[Any]:
    if variant == "flowinvoice":
        results = payload.get("results", payload.get("notices", []))
    else:
        results = payload.get("notices", payload.get("results", []))
    return results if isinstance(results, list) else []


def _ted_parse_item(item: Any, country: str, variant: str) -> dict[str, str]:
    content: Any = item if isinstance(item, dict) else {}
    if variant == "flowinvoice":
        nd = content.get("ND", content.get("noticeNumber", content.get("publicationNumber", "")))
        return _ted_notice(
            publication_number=str(nd),
            publication_date=content.get("PD", content.get("publicationDate", "")),
            notice_title=content.get("TI", content.get("title", content.get("noticeTitle", "")))[
                :200
            ],
            buyer_name=content.get(
                "OL", content.get("buyerName", content.get("organisationName", ""))
            ),
            buyer_country=content.get("CY", country),
            contract_type=content.get("NC", content.get("contractType", "")),
            procedure_type=content.get("PR", content.get("procedureType", "")),
            estimated_value=str(content.get("TV", content.get("totalValue", ""))),
            notice_type=content.get("TD", content.get("documentType", "")),
            url=f"https://ted.europa.eu/en/notice/{nd}" if nd else "",
        )
    cy = DESIGNER_COUNTRY_MAP.get(country.upper(), country.upper())
    nd = content.get("ND", content.get("publication-number", ""))
    return _ted_notice(
        publication_number=str(nd),
        publication_date=content.get("PD", ""),
        notice_title=_designer_title(content.get("TI", "")),
        buyer_name=content.get("OL", ""),
        buyer_country=cy,
        contract_type=content.get("NC", ""),
        procedure_type=content.get("PR", ""),
        estimated_value=str(content.get("TV", "")),
        notice_type=content.get("TD", ""),
        url=f"https://ted.europa.eu/en/notice/{nd}" if nd else "",
    )


def legacy_ted_company_parse(
    status: int, payload: Any, country: str, variant: str
) -> list[dict[str, str]]:
    """Source behavior: non-200 status or invalid JSON yields ``[]``; a parser error
    ends the loop and returns the notices parsed so far (errors are swallowed).

    ``payload`` is the decoded JSON body or the exception raised while decoding.
    """
    _check_variant(variant)
    if status != 200 or isinstance(payload, BaseException):
        return []
    notices: list[dict[str, str]] = []
    try:
        for item in _ted_items(payload, variant):
            notices.append(_ted_parse_item(item, country, variant))
    except Exception:  # noqa: BLE001 - source swallowed every parsing error
        return notices
    return notices


def ted_company_result(status: int, payload: Any, country: str, variant: str) -> SearchResult:
    """Corrected contract: HTTP errors, invalid JSON and parser errors are explicit failures."""
    _check_variant(variant)
    if status == 404:
        return SearchResult(STATUS_NO_HIT, variant=variant)
    if status == 429:
        return SearchResult(STATUS_RATE_LIMITED, error="HTTP 429", variant=variant)
    if status != 200:
        return SearchResult(STATUS_FAILED, error=f"HTTP {status}", variant=variant)
    if isinstance(payload, BaseException):
        return SearchResult(
            STATUS_FAILED, error=f"Antwort ist kein JSON: {payload}", variant=variant
        )
    if not isinstance(payload, Mapping):
        return SearchResult(STATUS_FAILED, error="Antwort ist kein JSON-Objekt", variant=variant)
    try:
        notices = tuple(_ted_parse_item(i, country, variant) for i in _ted_items(payload, variant))
    except (TypeError, AttributeError, KeyError, ValueError) as exc:
        return SearchResult(STATUS_FAILED, error=f"Parserfehler: {exc}", variant=variant)
    return SearchResult(STATUS_OK if notices else STATUS_NO_HIT, notices, variant=variant)


# ------------------------------------------------------------------- HAD


def had_request(company_name: str, include_archived: bool, variant: str) -> dict[str, Any]:
    """Request description of the HAD search form of the variant."""
    _check_variant(variant)
    return {
        "method": "GET",
        "url": HAD_SEARCH_URL[variant],
        "params": {"q": company_name, "archiv": "1" if include_archived else "0"},
        "headers": {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "EFRE-AuditTool/2.0",
        },
        "timeout": 20,
    }


def parse_had_html(content: bytes) -> list[dict[str, str]]:
    """Result rows of a HAD results page (heuristic columns of the source; needs ``lxml``).

    Raises:
        ImportError: install ``auditcore_procurement[html]``.
    """
    try:
        from lxml import html as lxml_html
    except ImportError as exc:  # pragma: no cover - depends on the optional extra
        raise ImportError("HAD-Parser benötigt auditcore_procurement[html] (lxml).") from exc
    tree = lxml_html.fromstring(content)
    rows = (
        tree.xpath('//table[contains(@class,"result")]//tr')
        or tree.xpath('//div[contains(@class,"search-result")]')
        or tree.xpath('//div[contains(@class,"ausschreibung")]')
    )
    notices: list[dict[str, str]] = []
    for row in rows:
        try:
            texts = [t.strip() for t in row.itertext() if t.strip()]
            if len(texts) < 2:
                continue
            notice = dict.fromkeys(HAD_NOTICE_FIELDS, "")
            notice.update(
                titel=texts[0],
                vergabestelle=texts[1],
                vergabeart=texts[2] if len(texts) > 2 else "",
                leistungsart=texts[3] if len(texts) > 3 else "",
                ort=texts[4] if len(texts) > 4 else "",
                datum=texts[-1],
            )
            links = row.xpath(".//a/@href")
            if links:
                link = str(links[0])
                notice["url"] = link if link.startswith("http") else f"https://www.had.de/{link}"
                match = re.search(r"id=(\d+)", link)
                if match:
                    notice["bekanntmachung_id"] = match.group(1)
            notices.append(notice)
        except Exception:  # noqa: BLE001, S112 - source skipped malformed rows
            continue
    return notices


def legacy_had_parse(
    status: int, content: bytes | BaseException, variant: str
) -> list[dict[str, str]]:
    """Source behavior of both variants: only HTTP 200 is parsed; everything else yields ``[]``."""
    _check_variant(variant)
    if status != 200 or isinstance(content, BaseException):
        return []
    try:
        return parse_had_html(content)
    except ImportError:
        raise
    except Exception:  # noqa: BLE001 - source swallowed every error
        return []


def had_result(status: int, content: bytes | BaseException, variant: str) -> SearchResult:
    """Corrected contract. HTTP 404 is ``no_hit`` only in the ``designer`` variant
    (source semantics); in ``flowinvoice`` it is a failure. 403 is rate limiting."""
    _check_variant(variant)
    if isinstance(content, BaseException):
        return SearchResult(STATUS_FAILED, error=str(content), variant=variant)
    if status == 404 and variant == "designer":
        return SearchResult(STATUS_NO_HIT, variant=variant)
    if status in (403, 429):
        return SearchResult(STATUS_RATE_LIMITED, error=f"HTTP {status}", variant=variant)
    if status != 200:
        return SearchResult(STATUS_FAILED, error=f"HTTP {status}", variant=variant)
    notices = tuple(parse_had_html(content))
    warnings = () if notices else ("Keine Ergebniszeilen erkannt; Seitenlayout prüfen.",)
    return SearchResult(
        STATUS_OK if notices else STATUS_NO_HIT, notices, variant=variant, warnings=warnings
    )
