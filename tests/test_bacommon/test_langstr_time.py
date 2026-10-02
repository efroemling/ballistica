# Released under the MIT License. See LICENSE for details.
#
"""Tests for time-varying language-strings (time targets) and spec'd
tokens in literal templates."""

import datetime

from efro.dataclassio import dataclass_to_json, dataclass_from_json
from bacommon.assetpackage import ApverNum
from bacommon.locale import Locale
from bacommon.langstr import (
    LangStrSpec,
    LangStrSpecResource,
    LangStrSpecValue,
    LangStrSpecTimeTarget,
    LanguageStringNameDecodeContext,
    LanguageStringEncodeContext,
    PackageStructure,
    LangStrError,
    convert_time_subs,
    literal_template_kinds,
)

_PKG = ApverNum(101)

#: English duration and data-size unit words, as a package embeds them.
_COMPONENTS: dict[str, object] = {
    'duration/years': '{amount}y',
    'duration/days': '{amount}d',
    'duration/hours': '{amount}h',
    'duration/minutes': '{amount}m',
    'duration/seconds': '{amount}s',
    'data_size/kilobytes': '{amount} KB',
}

_NOW = datetime.datetime(2026, 10, 1, 12, 0, 0, tzinfo=datetime.UTC)


def _ctx() -> LanguageStringNameDecodeContext:
    return LanguageStringNameDecodeContext(
        {_PKG: {'ends': 'Ends in {t}', 'hello': 'Hello {name}'}},
        Locale.ENGLISH,
        param_kinds={_PKG: {'ends': {'t': 'millis(dir=future)'}}},
        components={_PKG: _COMPONENTS},  # type: ignore[dict-item]
        now=_NOW,
    )


def _at(**kwargs: float) -> LangStrSpecTimeTarget:
    return LangStrSpecTimeTarget.at(_NOW + datetime.timedelta(**kwargs))


def test_literal_template_kinds() -> None:
    """Spec'd tokens reduce to plain tokens plus their kinds."""
    assert literal_template_kinds('plain {x}') == ('plain {x}', {})
    assert literal_template_kinds('In {t|duration(dir=future)}!') == (
        'In {t}!',
        {'t': 'millis(dir=future)'},
    )
    assert literal_template_kinds('{s|data_size} {{t|duration}}') == (
        '{s} {{t|duration}}',
        {'s': 'bytes'},
    )
    for bad in ('{t|nope}', '{t|duration(dir=up)}', '{n|plural}'):
        try:
            literal_template_kinds(bad)
        except LangStrError:
            pass
        else:
            raise AssertionError(f'no error for {bad!r}')


def test_time_target_decode() -> None:
    """Time targets render as their offset from now via the param spec."""
    ctx = _ctx()
    ends = LangStrSpecResource(_PKG, 'ends', {'t': _at(minutes=4, seconds=12)})
    assert ctx.decode(ends) == 'Ends in 4m 12s'
    # Countdowns round up to their smallest unit shown.
    for kwargs, expected in (
        ({'seconds': 0.4}, 'Ends in 1s'),
        ({'minutes': 59, 'seconds': 59.5}, 'Ends in 1h 0m'),
        ({'hours': 1, 'seconds': 0.5}, 'Ends in 1h 1m'),
        ({'minutes': 4, 'seconds': 12}, 'Ends in 4m 12s'),
    ):
        spec = LangStrSpecResource(_PKG, 'ends', {'t': _at(**kwargs)})
        assert ctx.decode(spec) == expected, kwargs
    tenths = LangStrSpecValue(
        '{t|duration(dir=future,decimals=1)}', {'t': _at(seconds=12.34)}
    )
    assert ctx.decode(tenths) == '12.4s'
    # A countdown rests at zero once its moment passes.
    past = LangStrSpecResource(_PKG, 'ends', {'t': _at(seconds=-30)})
    assert ctx.decode(past) == 'Ends in 0s'
    # Literal templates declare their own specs.
    lit = LangStrSpecValue(
        'Up {t|duration(dir=past,decimals=1)}', {'t': _at(seconds=-3.25)}
    )
    assert ctx.decode(lit) == 'Up 3.2s'
    # Plain ints still mean a fixed length.
    fixed = LangStrSpecValue('{t|duration}', {'t': 90_000})
    assert ctx.decode(fixed) == '1m 30s'
    # A time target anywhere but a duration param is an error.
    bad = LangStrSpecResource(_PKG, 'hello', {'name': _at(seconds=5)})
    assert ctx.decode(bad).startswith('LANGSTR_ERROR:')
    assert ctx.decode(_at(seconds=5)).startswith('LANGSTR_ERROR:')


def test_time_target_wire() -> None:
    """Time targets round-trip and pass through index conversion."""
    spec: LangStrSpec = LangStrSpecResource(_PKG, 'ends', {'t': _at(hours=1)})
    assert dataclass_from_json(LangStrSpec, dataclass_to_json(spec)) == spec
    struct = PackageStructure(_PKG, {'ends': ('t',)})
    enc = LanguageStringEncodeContext([spec], {_PKG: struct})
    indexed = enc.to_indexed(spec)
    assert dataclass_from_json(LangStrSpec, dataclass_to_json(indexed)) == (
        indexed
    )
    # Chunks have no slot for a live moment; they get the fixed length.
    future: LangStrSpec = LangStrSpecResource(
        _PKG,
        'ends',
        {
            't': LangStrSpecTimeTarget.at(
                datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(hours=1)
            )
        },
    )
    chunk = enc.encode(future)
    assert isinstance(chunk[2], int) and 3_500_000 < chunk[2] <= 3_600_000


def test_wrapper_time_subs() -> None:
    """Wrappers keep a datetime live unless given a ``now``."""
    moment = _NOW + datetime.timedelta(minutes=5)
    live = convert_time_subs({'t': moment})
    assert live == {'t': LangStrSpecTimeTarget.at(moment)}
    frozen = convert_time_subs({'t': moment}, now=_NOW)
    assert frozen == {'t': 300_000}
    length = convert_time_subs({'t': datetime.timedelta(seconds=2)})
    assert length == {'t': 2000}
