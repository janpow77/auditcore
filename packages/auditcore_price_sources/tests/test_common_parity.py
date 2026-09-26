"""Parity old ↔ new: package bytes after the move to ``auditcore_common``.

``canonical_json_bytes`` determines the package hashes regulierung logs per
run. The legacy copy below is the 0.1.2 implementation verbatim; every fixed
fixture must give the same bytes, and the digests are pinned so that a drift
of both sides (e.g. in ``auditcore_common``) is caught as well.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from auditcore_price_sources import canonical_json_bytes, package_sha256

PAYLOADS = Path(__file__).parent / "fixtures" / "payloads"

#: Synthetic edge bodies: ASCII escapes, float/int forms, NaN, whitespace, scalars.
EDGE_BODIES = {
    "edge0": b'{"b": 1, "a": [1.0, 2.5e-10, 1e100, -0.0, 12345678901234567890]}',
    "edge1": '{"ö": "Ärger – € 😀", "z": null, "a": {"y": true, "x": false}}'.encode(),
    "edge2": b'[NaN, Infinity, -Infinity, "\\u00e9"]',
    "edge3": b'  {"nested": {"k": [{"b": 2, "a": 1}]}}  \n',
    "edge4": b'"text"',
    "edge5": b"0",
}

#: SHA-256 of the canonical bytes, recorded with the legacy implementation.
#: Five of them equal ``paket_sha256`` in regulierung_connectors_observed.json.
PINNED = {
    "bundesbank_empty.json": "82a3e4fbf51ce50f65d6ce578af9768c9c3dd6d7ca3fe72ba9afaeac5d6ebfc1",
    "bundesbank_fx.json": "2a8cd8f9f22dccfebfe59de60521ce25dca38907da285c8a5d50ca5d5706f6b1",
    "bundesbank_fx_clean.json": "22c9b8a95d4373f138013ee3e6c732b2cf052cfe8d8e1b62f869d7ad30d29b86",
    "eia_brent.json": "9e861ba865ece28f21352668db958b6c3ea6beb84553588656269004fac522d0",
    "eia_brent_clean_page1.json": (
        "3d007252df5b6e7d872c179d49f1eececc0ff91a00654560ddb1c2e3fc43291a"
    ),
    "eia_brent_clean_page2.json": (
        "c669baff86f03b7567ed4d0d9d7355d5d4b091eec5b6543ebfa582cb9928ff58"
    ),
    "eia_brent_page1.json": "f34d999622fe8f4ece0347615dfef8e98e20819963c8fdf78d4b6606bd132fa0",
    "eia_brent_page2.json": "9c8b01d97e7d879cb4d8b919527d40f937bf14e50e25690190043b899d5111db",
    "overpass_fuel.json": "a219f8ab55a43a486a52a7ae3ca18356b6c78190ec0b5764e1b6b3a31d3e70d1",
    "overpass_fuel_clean.json": "60ed667061b8a6951a4bc35c6d4cbef6c0e8c2dc8167ea33ffcbc28ae8dc0d29",
    "overpass_remark.json": "67375c384a1e0b862a54a3dc391545615edcc3b0bdd980d57d3543c352ca9dda",
    "tankerkoenig_error.json": "a7799333be502d2f43bda36bae34f6f0269cafdda29dfbfe4527241e20520df2",
    "tankerkoenig_list.json": "d98768e7b3663086a40b991c4489d6fad363f7e0257c5c5a5b21ba7b86712972",
    "edge0": "83e2f84bee8b7209eeeb17752eb1583632712412d1cde431b1ce88b74c4bf6da",
    "edge1": "f6e0be009b8c6ce2b4a00852120c5799fe14cb3c08e44b6eafe69d760b03b201",
    "edge2": "73cf21df83cb6e7d3167550ea3b45cc2f18f757d98b2451f79d4741d362e4452",
    "edge3": "06fbdd4094ba9c5e2c2cbdc851ff18a63cf46376de299def866be43b7a049d97",
    "edge4": "1e1d0f251d3a76fa2b1bfc81164078572623403887db02988b504b0492e9f076",
    "edge5": "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9",
}


# auditcore_price_sources 0.1.2, snapshots.py :: canonical_json_bytes (verbatim)
def legacy_canonical_json_bytes(body: bytes) -> bytes:
    return json.dumps(json.loads(body), sort_keys=True).encode()


def _bodies() -> dict[str, bytes]:
    bodies = {p.name: p.read_bytes() for p in sorted(PAYLOADS.glob("*.json"))}
    return {**bodies, **EDGE_BODIES}


def test_every_fixture_is_pinned() -> None:
    assert set(_bodies()) == set(PINNED)


@pytest.mark.parametrize("name", sorted(PINNED))
def test_canonical_bytes_are_byte_identical(name: str) -> None:
    body = _bodies()[name]
    new = canonical_json_bytes(body)
    assert new == legacy_canonical_json_bytes(body)
    assert hashlib.sha256(new).hexdigest() == PINNED[name]
    assert package_sha256(body, canonical_json=True) == PINNED[name]


@pytest.mark.parametrize("body", [b"", b"{", b"not json", b'{"a": }'])
def test_invalid_json_fails_identically(body: bytes) -> None:
    with pytest.raises(ValueError) as new:
        canonical_json_bytes(body)
    with pytest.raises(ValueError) as old:
        legacy_canonical_json_bytes(body)
    assert type(new.value) is type(old.value)
    assert str(new.value) == str(old.value)
