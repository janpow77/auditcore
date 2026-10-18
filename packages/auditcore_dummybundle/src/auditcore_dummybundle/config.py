"""Run parameters of a bundle: strict reading, defaults and limits.

The defaults are settings of the generator, not rules of any programme: the
public share, the Union co-financing rate and the value limit for direct
awards are parameters the caller chooses.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal

from auditcore_dummybundle import parsing
from auditcore_dummybundle.errors import BundleError

FUNDS = ("EFRE", "ESF+", "Kohäsionsfonds", "JTF")
COUNTRY_CHOICES = ("DE", "AT", "DE+AT")
VAT_MODES = ("yes", "no", "mixed")
PERSON_MODES = ("roles", "catalog")
_UNIT = (Decimal(0), Decimal(1))


@dataclass(frozen=True)
class BundleLimits:
    """Upper bounds a host may tighten for a public endpoint."""

    max_operations: int = 200
    max_claims: int = 6
    max_receipts: int = 40
    max_corrections: int = 50


@dataclass(frozen=True)
class BundleConfig:
    """Everything that determines a bundle; equal configurations give equal bundles."""

    seed: int
    base_date: date
    country: str = "DE"
    fund: str = "EFRE"
    operations: int = 5
    claims_min: int = 1
    claims_max: int = 3
    receipts_min: int = 5
    receipts_max: int = 12
    priorities: int = 2
    payment_applications: int = 3
    public_share: Decimal = Decimal("0.75")
    eu_rate: Decimal = Decimal("0.40")
    vat_deduction: str = "mixed"
    discount_share: Decimal = Decimal("0.30")
    reduction_share: Decimal = Decimal("0.10")
    corrections: int = 4
    prior_year_withdrawals: int = 1
    direct_award_limit: Decimal = Decimal("1000.00")
    identifiers_valid: bool = False
    person_names: str = "roles"
    anomalies: tuple[str, ...] = ()
    anomaly_rate: Decimal = Decimal("0.05")

    def as_dict(self) -> dict[str, object]:
        """JSON-ready parameters in the form :func:`parse_config` reads."""
        data: dict[str, object] = {}
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, (date, Decimal)):
                data[item.name] = str(value)
            elif isinstance(value, tuple):
                data[item.name] = list(value)
            else:
                data[item.name] = value
        return data


def accounting_year(base_date: date) -> tuple[date, date]:
    """Accounting year (1 July to 30 June) that contains ``base_date``."""
    start_year = base_date.year if base_date.month >= 7 else base_date.year - 1
    return date(start_year, 7, 1), date(start_year + 1, 6, 30)


def _counts(raw: dict[str, object], limits: BundleLimits) -> dict[str, int]:
    ranges = {
        "operations": (1, limits.max_operations),
        "claims_min": (1, limits.max_claims),
        "claims_max": (1, limits.max_claims),
        "receipts_min": (1, limits.max_receipts),
        "receipts_max": (1, limits.max_receipts),
        "priorities": (1, 6),
        "payment_applications": (1, 6),
        "corrections": (0, limits.max_corrections),
        "prior_year_withdrawals": (0, 5),
    }
    return {
        key: parsing.as_int(raw[key], key, low, high)
        for key, (low, high) in ranges.items()
        if key in raw
    }


def _rates(raw: dict[str, object]) -> dict[str, Decimal]:
    keys = ("public_share", "eu_rate", "discount_share", "reduction_share", "anomaly_rate")
    values = {key: parsing.as_decimal(raw[key], key, *_UNIT) for key in keys if key in raw}
    if "direct_award_limit" in raw:
        values["direct_award_limit"] = parsing.as_decimal(
            raw["direct_award_limit"], "direct_award_limit", Decimal(1), Decimal(10_000_000)
        ).quantize(Decimal("0.01"))
    return values


def _choices(raw: dict[str, object]) -> dict[str, str]:
    options = {
        "country": COUNTRY_CHOICES,
        "fund": FUNDS,
        "vat_deduction": VAT_MODES,
        "person_names": PERSON_MODES,
    }
    return {
        key: parsing.as_choice(raw[key], key, allowed)
        for key, allowed in options.items()
        if key in raw
    }


def _anomalies(raw: dict[str, object], anomaly_codes: tuple[str, ...]) -> tuple[str, ...]:
    if "anomalies" not in raw:
        return ()
    codes = parsing.as_list(raw["anomalies"], "anomalies", len(anomaly_codes))
    chosen = [parsing.as_choice(code, "anomalies", anomaly_codes) for code in codes]
    return tuple(code for code in anomaly_codes if code in chosen)


def parse_config(
    raw: object,
    *,
    anomaly_codes: tuple[str, ...] = (),
    limits: BundleLimits | None = None,
) -> BundleConfig:
    """Strictly read run parameters; ``seed`` and ``base_date`` are mandatory."""
    allowed = {item.name for item in fields(BundleConfig)}
    data = dict(parsing.as_object(raw, "params", allowed))
    for key in ("seed", "base_date"):
        if key not in data:
            raise BundleError(f"'{key}' fehlt.", code="missing", path=key)
    config = _assemble(
        BundleConfig(
            seed=parsing.as_int(data["seed"], "seed", 0, 2**31 - 1),
            base_date=parsing.as_date(data["base_date"], "base_date"),
            anomalies=_anomalies(data, anomaly_codes),
            identifiers_valid=parsing.as_bool(
                data.get("identifiers_valid", False), "identifiers_valid"
            ),
        ),
        _counts(data, limits or BundleLimits()),
        _rates(data),
        _choices(data),
    )
    _check_consistency(config)
    return config


def _assemble(
    base: BundleConfig, counts: dict[str, int], rates: dict[str, Decimal], choices: dict[str, str]
) -> BundleConfig:
    """``base`` with the given counts, rates and choices; missing keys keep the default."""
    return BundleConfig(
        seed=base.seed,
        base_date=base.base_date,
        anomalies=base.anomalies,
        identifiers_valid=base.identifiers_valid,
        country=choices.get("country", base.country),
        fund=choices.get("fund", base.fund),
        vat_deduction=choices.get("vat_deduction", base.vat_deduction),
        person_names=choices.get("person_names", base.person_names),
        operations=counts.get("operations", base.operations),
        claims_min=counts.get("claims_min", base.claims_min),
        claims_max=counts.get("claims_max", base.claims_max),
        receipts_min=counts.get("receipts_min", base.receipts_min),
        receipts_max=counts.get("receipts_max", base.receipts_max),
        priorities=counts.get("priorities", base.priorities),
        payment_applications=counts.get("payment_applications", base.payment_applications),
        corrections=counts.get("corrections", base.corrections),
        prior_year_withdrawals=counts.get("prior_year_withdrawals", base.prior_year_withdrawals),
        public_share=rates.get("public_share", base.public_share),
        eu_rate=rates.get("eu_rate", base.eu_rate),
        discount_share=rates.get("discount_share", base.discount_share),
        reduction_share=rates.get("reduction_share", base.reduction_share),
        anomaly_rate=rates.get("anomaly_rate", base.anomaly_rate),
        direct_award_limit=rates.get("direct_award_limit", base.direct_award_limit),
    )


def _check_consistency(config: BundleConfig) -> None:
    if config.claims_min > config.claims_max:
        raise BundleError("'claims_min' darf 'claims_max' nicht übersteigen.", path="claims_min")
    if config.receipts_min > config.receipts_max:
        raise BundleError(
            "'receipts_min' darf 'receipts_max' nicht übersteigen.", path="receipts_min"
        )
    if config.eu_rate > config.public_share:
        raise BundleError(
            "'eu_rate' darf den öffentlichen Anteil 'public_share' nicht übersteigen.",
            path="eu_rate",
        )
