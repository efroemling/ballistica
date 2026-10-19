# Released under the MIT License. See LICENSE for details.
#
"""Tests for joining language-string specs (LangStrSpecValue.join)."""

import pytest

from efro.dataclassio import dataclass_to_json, dataclass_from_json
from bacommon.assetpackage import ApverNum
from bacommon.locale import Locale
from bacommon.langstr import (
    MAX_JOIN_ITEMS,
    MAX_NESTING_DEPTH,
    LangStrSpec,
    LangStrSpecResource,
    LangStrSpecValue,
    LanguageStringNameDecodeContext,
)

_PKG = ApverNum(101)


def _ctx() -> LanguageStringNameDecodeContext:
    return LanguageStringNameDecodeContext(
        {_PKG: {'hello': 'Hello {name}', 'bye': 'Goodbye'}},
        Locale.ENGLISH,
    )


def test_join_structure() -> None:
    """Join builds what the native LangStr.join does: an i0/i1 template."""
    hello = LangStrSpecResource(_PKG, 'hello', {'name': 'Eric'})
    bye = LangStrSpecResource(_PKG, 'bye')
    out = LangStrSpecValue.join([hello, bye], '\n')
    assert out.value == '{i0}\n{i1}'
    assert out.subs == {'i0': hello, 'i1': bye}


def test_join_renders() -> None:
    """Each item renders in place, translated, around the separator."""
    hello = LangStrSpecResource(_PKG, 'hello', {'name': 'Eric'})
    bye = LangStrSpecResource(_PKG, 'bye')
    lit = LangStrSpecValue.literal('{not a token}')
    out = LangStrSpecValue.join([hello, lit, bye], ' | ')
    assert _ctx().decode(out) == 'Hello Eric | {not a token} | Goodbye'


def test_join_separator_is_literal() -> None:
    """Separator braces display as-is rather than forming tokens."""
    items: list[LangStrSpec] = [
        LangStrSpecValue.literal('a'),
        LangStrSpecValue.literal('b'),
    ]
    out = LangStrSpecValue.join(items, ' {i0} ')
    assert _ctx().decode(out) == 'a {i0} b'


def test_join_edge_counts() -> None:
    """No items gives empty text; one item gives just that item."""
    assert _ctx().decode(LangStrSpecValue.join([], ', ')) == ''
    one = LangStrSpecValue.join([LangStrSpecValue.literal('x')], ', ')
    assert _ctx().decode(one) == 'x'


def test_join_limits() -> None:
    """Too many items, or too deep a result, is refused."""
    item = LangStrSpecValue.literal('x')
    LangStrSpecValue.join([item] * MAX_JOIN_ITEMS)
    with pytest.raises(ValueError):
        LangStrSpecValue.join([item] * (MAX_JOIN_ITEMS + 1))

    # Nest joins until the next one would be one level too deep.
    deep: LangStrSpec = item
    for _ in range(MAX_NESTING_DEPTH):
        deep = LangStrSpecValue.join([deep])
    with pytest.raises(ValueError):
        LangStrSpecValue.join([deep])


def test_join_wire_round_trip() -> None:
    """A joined spec survives the wire like any other value spec."""
    out = LangStrSpecValue.join(
        [
            LangStrSpecResource(_PKG, 'hello', {'name': 'Eric'}),
            LangStrSpecResource(_PKG, 'bye'),
        ],
        '\n',
    )
    back = dataclass_from_json(LangStrSpec, dataclass_to_json(out))
    assert back == out
