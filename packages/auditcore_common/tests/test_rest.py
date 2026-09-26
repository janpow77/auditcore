"""REST contract helpers equal the former package copies (differential)."""

from __future__ import annotations

import json
import random
from collections.abc import Callable
from decimal import Decimal

import legacy_rest as legacy
import pytest
from samples import SAMPLES, TEXTS, random_json, rng, same

from auditcore_common import rest


class SamplingError(rest.ContractError):
    """Package subclass as the sampling package defines it."""


class StatisticsError(rest.ContractError):
    """Package subclass as the statistics package defines it."""


class IdentifiersError(rest.ContractError):
    """Package subclass as the identifiers package defines it."""


class ReportingError(rest.ContractError):
    """Package subclass as the reporting package defines it."""


class GeoError(rest.ContractError):
    """Package subclass as the geo package defines it (own default code)."""

    def __init__(
        self, message: str, *, status: int = 422, code: str = "ungueltige_eingabe"
    ) -> None:
        super().__init__(message, status=status, code=code)


Outcome = tuple[str, object]


def _outcome(function: Callable[[], object]) -> Outcome:
    """Result, or status/code/message/body/cause of a contract error."""
    try:
        return ("ok", function())
    except (
        rest.ContractError,
        legacy.SamplingContractError,
        legacy.StatisticsContractError,
        legacy.IdentifiersContractError,
        legacy.ReportingContractError,
        legacy.GeoContractError,
    ) as exc:
        cause = type(exc.__cause__).__name__ if exc.__cause__ else None
        return ("error", (exc.status, exc.code, str(exc), exc.to_dict(), cause))


def _reply(reply: object) -> tuple[object, ...]:
    """Comparable fields of an old or new reply; missing headers mean none."""
    headers = dict(getattr(reply, "headers", {}))
    return (reply.status, reply.body, reply.media_type, headers)  # type: ignore[attr-defined]


def _assert_same(old: Callable[[], object], new: Callable[[], object]) -> None:
    expected, actual = _outcome(old), _outcome(new)
    assert expected[0] == actual[0], (expected, actual)
    assert same(expected[1], actual[1]), (expected, actual)


def random_body(r: random.Random) -> bytes:
    """Valid JSON, broken JSON, invalid UTF-8 and empty bodies."""
    kind = r.randrange(6)
    if kind == 0:
        return json.dumps(random_json(r), allow_nan=True).encode()
    if kind == 1:
        return json.dumps(random_json(r), ensure_ascii=False).encode("utf-8")
    if kind == 2:
        return json.dumps(random_json(r)).encode()[: r.randint(0, 20)]
    if kind == 3:
        return bytes(r.getrandbits(8) for _ in range(r.randint(0, 12)))
    if kind == 4:
        return r.choice((b"", b" ", b"1.10", b"1e400", b"-0.0", b"NaN", b'"\xc3\xa4"', b"\xff"))
    return r.choice(TEXTS).encode("utf-8")


def test_contract_error_matches_both_copies() -> None:
    for kwargs in ({}, {"status": 413}, {"code": "too_large"}, {"status": 400, "code": "x"}):
        for message in ("", "Pflichtfeld 'x' fehlt.", "Ä"):
            new = SamplingError(message, **kwargs)  # type: ignore[arg-type]
            for old in (
                legacy.SamplingContractError(message, **kwargs),  # type: ignore[arg-type]
                legacy.StatisticsContractError(message, **kwargs),  # type: ignore[arg-type]
            ):
                assert (new.status, new.code, str(new), new.args) == (
                    old.status,
                    old.code,
                    str(old),
                    old.args,
                )
                assert new.to_dict() == old.to_dict()
            assert isinstance(new, ValueError)


def test_json_reply_matches_both_copies() -> None:
    r = rng(71)
    for _ in range(SAMPLES):
        data = random_json(r)
        status = r.choice((200, 400, 413, 422))
        for old in (legacy.sampling_json, legacy.statistics_json):
            _assert_same(
                lambda: _reply(old(status, data)),  # noqa: B023 - called immediately
                lambda: _reply(rest.json_reply(status, data)),
            )


def test_decode_matches_both_copies() -> None:
    r = rng(72)
    for _ in range(SAMPLES):
        raw = random_body(r)
        limit = r.choice((0, 1, 5, len(raw), len(raw) - 1, 1 << 20))
        _assert_same(
            lambda: legacy.sampling_decode(raw, limit),
            lambda: rest.decode_body(raw, limit, error=SamplingError),
        )
        _assert_same(
            lambda: legacy.statistics_decode(raw, limit),
            lambda: rest.decode_body(raw, limit, error=StatisticsError, parse_float=Decimal),
        )


def _handler(error: type[ValueError]) -> Callable[[object], dict[str, object]]:
    """Endpoint stand-in: echoes objects, rejects everything else with ``error``."""

    def run(payload: object) -> dict[str, object]:
        if isinstance(payload, dict):
            return {"keys": list(payload)}
        raise error("Die Anfrage muss ein JSON-Objekt sein.")

    return run


def _new_dispatch(
    raw: bytes, limit: int, error: type[rest.ContractError], parse_float: type[Decimal] | None
) -> rest.Reply:
    def action() -> rest.Reply:
        payload = rest.decode_body(raw, limit, error=error, parse_float=parse_float)
        return rest.json_reply(200, _handler(error)(payload))

    return rest.guarded(action, error=error)


def test_guarded_dispatch_matches_both_copies() -> None:
    r = rng(73)
    for _ in range(SAMPLES):
        raw = random_body(r)
        limit = r.choice((3, 1 << 20))
        _assert_same(
            lambda: _reply(
                legacy.sampling_handle(_handler(legacy.SamplingContractError), raw, limit)
            ),
            lambda: _reply(_new_dispatch(raw, limit, SamplingError, None)),
        )
        _assert_same(
            lambda: _reply(
                legacy.statistics_handle_analyse(
                    _handler(legacy.StatisticsContractError), raw, limit
                )
            ),
            lambda: _reply(_new_dispatch(raw, limit, StatisticsError, Decimal)),
        )


def test_guarded_lets_foreign_errors_through() -> None:
    def fail() -> rest.Reply:
        raise StatisticsError("fremd")

    with pytest.raises(StatisticsError):
        rest.guarded(fail, error=SamplingError)
    assert rest.guarded(fail).status == 422


ALLOWED = (("proportional", "equal"), ("first", "first_two", "second"), ("exclude", "pad"), ())


def test_choice_matches_both_copies() -> None:
    r = rng(74)
    candidates: list[object] = [None, 1, 1.0, True, [], {}, "", "Equal", *TEXTS]
    for allowed in ALLOWED:
        candidates.extend(allowed)
    for _ in range(SAMPLES):
        allowed = r.choice(ALLOWED)
        value = r.choice(candidates)
        name = r.choice(("method", "test", "profile", "short_values", "Ä"))
        _assert_same(
            lambda: legacy.sampling_choice(value, name, allowed),
            lambda: rest.choice(value, name, allowed, error=SamplingError),
        )
        body = {} if value is None and r.random() < 0.5 else {name: value}
        _assert_same(
            lambda: legacy.statistics_field(body, name, allowed),
            lambda: rest.choice(body.get(name), name, allowed, error=StatisticsError),
        )


def test_bounded_list_matches_both_copies() -> None:
    r = rng(75)
    shapes: list[object] = [None, [], {}, "x", (1,), 0, [None], [1, 2], {"a": 1}]
    for _ in range(SAMPLES // 4):
        raw = r.choice(shapes) if r.random() < 0.5 else [random_json(r) for _ in range(5)]
        _assert_same(
            lambda: legacy.sampling_parse_items(raw),
            lambda: rest.bounded_list(
                raw, "items", legacy.MAX_ITEMS, "Elemente", error=SamplingError
            ),
        )
        _assert_same(
            lambda: legacy.statistics_values(raw),
            lambda: rest.bounded_list(
                raw, "values", legacy.MAX_VALUES, "Werte", error=StatisticsError
            ),
        )


@pytest.mark.parametrize("size", [legacy.MAX_ITEMS, legacy.MAX_ITEMS + 1])
def test_bounded_list_limit_edges(size: int) -> None:
    raw: list[object] = [0] * size
    _assert_same(
        lambda: legacy.sampling_parse_items(raw),
        lambda: rest.bounded_list(raw, "items", legacy.MAX_ITEMS, "Elemente", error=SamplingError),
    )


def test_json_object_matches_both_copies() -> None:
    r = rng(76)
    shapes: list[object] = [None, [], {}, "x", 0, 1.5, True, {1: "a"}, {"a": 1, 2: "b"}, {"ä": []}]
    for _ in range(SAMPLES):
        value = r.choice(shapes) if r.random() < 0.5 else random_json(r)
        path = r.choice(("Anfrage", "items[0]", "sheets[3].labels", "Ä", ""))
        _assert_same(
            lambda: legacy.identifiers_object(value, path),
            lambda: rest.json_object(value, path, error=IdentifiersError),
        )
        _assert_same(
            lambda: legacy.reporting_object(value, path),
            lambda: rest.json_object(value, path, error=ReportingError),
        )


def test_json_object_returns_the_same_mapping() -> None:
    body = {"a": 1}
    assert rest.json_object(body, "Anfrage") is body
    with pytest.raises(rest.ContractError, match="'x' muss ein JSON-Objekt sein."):
        rest.json_object([], "x")


def test_json_object_matches_sampling_geo_and_extrapolation() -> None:
    r = rng(77)
    shapes: list[object] = [None, [], {}, "x", 0, 1.5, True, {1: "a"}, {"a": 1, 2: "b"}, {"ä": []}]
    for _ in range(SAMPLES):
        value = r.choice(shapes) if r.random() < 0.5 else random_json(r)
        path = r.choice(("Anfrage", "items[0]", "strata", "punkte[2].lage", "Ä", ""))
        _assert_same(
            lambda: legacy.sampling_as_object(value, path),
            lambda: rest.json_object(value, path, error=SamplingError),
        )
        _assert_same(
            lambda: legacy.extrapolation_reader_body(value, path),
            lambda: rest.json_object(value, path, error=SamplingError),
        )
        _assert_same(
            lambda: legacy.geo_body_of(value, path),
            lambda: rest.json_object(value, path, error=GeoError),
        )


def test_geo_decode_and_reply_match_the_former_copy() -> None:
    r = rng(78)
    limit = 64
    bodies = [b"", b"{", b"\xff\xfe", b"[1, 2]", b'{"a": 1.5}', b"x" * (limit + 1), b"1" * limit]
    for _ in range(SAMPLES // 4):
        raw = r.choice(bodies) if r.random() < 0.5 else json.dumps(random_json(r)).encode()
        _assert_same(
            lambda: legacy.geo_decode(raw, limit),
            lambda: rest.decode_body(
                raw,
                limit,
                error=GeoError,
                too_large_code="zu_gross",
                invalid_json_code="ungueltiges_json",
            ),
        )
        data = random_json(r)
        old, new = legacy.geo_json(200, data), rest.json_reply(200, legacy.geo_clean(data))
        assert (old.status, old.body) == (new.status, new.body)
        assert new.media_type == "application/json" and dict(new.headers) == {}


def test_geo_error_keeps_its_default_code() -> None:
    old, new = legacy.GeoContractError("x"), GeoError("x")
    assert (old.status, old.code, old.to_dict()) == (new.status, new.code, new.to_dict())
