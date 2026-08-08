# Released under the MIT License. See LICENSE for details.
#
"""Parity tests for the native babase.LangStr against the Python impl.

Builds language-string trees with :mod:`bacommon.langstr`, serializes
them to canonical wire JSON, and runs a script inside the app
environment (via :func:`batools.apprun.python_command`) that parses
each with the native ``babase.LangStr`` and asserts evaluation and
round-trip parity with the Python implementation.
"""

import os

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

# Runs inside the app python environment (bacommon + babase available).
_PARITY_SCRIPT = """
import babase
from efro.dataclassio import dataclass_to_json, dataclass_from_json
from bacommon.langstr import (
    LangStrSpec,
    LangStrSpecResource,
    LangStrSpecValue,
    LangStrSpecResourceIndexed,
    LanguageStringNameDecodeContext,
)
from bacommon.locale import Locale

# Value-form cases evaluate fully native (no tables needed); expected
# values come from the Python evaluator, so this asserts parity, not
# hand-maintained outputs.
value_cases: list[LangStrSpec] = [
    LangStrSpecValue('Hello There.'),
    LangStrSpecValue('Hello {name}.', {'name': 'Flopsy'}),
    LangStrSpecValue('{a} and {b} make {total}.', {'a': 1, 'b': 2, 'total': 3}),
    LangStrSpecValue(
        'Nested: {inner}!',
        {'inner': LangStrSpecValue('{x} rules', {'x': 'recursion'})},
    ),
    LangStrSpecValue('Non-token braces stay literal: {Weird} {9foo} { } {x'),
    # Escaped braces: {{ -> { and }} -> }, even around a token pattern.
    LangStrSpecValue('Score {{x}} pts and {{y}}.'),
    LangStrSpecValue('Mixed {name} with {{lit}}.', {'name': 'Bo'}),
    LangStrSpecValue('Unicode: \\u3053\\u3093\\u306b\\u3061\\u306f {who}',
                 {'who': '\\u4e16\\u754c'}),
]
pyctx = LanguageStringNameDecodeContext({}, Locale.ENGLISH)
for case in value_cases:
    # Python impl requires all matching tokens present; mirror-check
    # only cases the Python side evaluates cleanly.
    expected = pyctx.decode(case)
    assert not expected.startswith('LANGSTR_ERROR:'), expected
    native = babase.LangStr(dataclass_to_json(case))
    got = native.evaluate()
    assert got == expected, f'{got!r} != {expected!r} for {case}'

# babase.LangStr.from_text wraps arbitrary text as a literal: any
# brace survives, including a token-shaped run, on both the native
# round-trip and the Python-side escape derivation.
for text in ['ModGame', '100% {x} done', '{v}', '{{already}}', 'C#', 'no{']:
    got = babase.LangStr.from_text(text).evaluate()
    assert got == text, f'from_text: {got!r} != {text!r}'

# ...and its wire form parses/evaluates identically through the Python
# decode path, confirming the escape convention matches.
ft_json = babase.LangStr.from_text('a {b} c').to_json()
assert pyctx.decode(dataclass_from_json(LangStrSpec, ft_json)) == 'a {b} c'

# Missing-substitution is fail-visible on both sides.
missing = LangStrSpecValue('Hi {name}.')
assert pyctx.decode(missing).startswith('LANGSTR_ERROR:')
assert babase.LangStr(dataclass_to_json(missing)).evaluate().startswith(
    'LANGSTR_ERROR:'
)

# Resource/indexed forms round-trip losslessly through the native
# parse (evaluation of these awaits the native table store).
rt_cases: list[LangStrSpec] = [
    LangStrSpecResource('a-0.testpkg.1a2b', 'common.hello_there'),
    LangStrSpecResource(
        'a-0.testpkg.1a2b',
        'common.hello_num',
        {'num': 5, 'name': LangStrSpecValue('Zoe')},
    ),
    LangStrSpecResourceIndexed(pkg=0, index=12),
    LangStrSpecResourceIndexed(
        pkg=1, index=0, subs=['x', 3, LangStrSpecResourceIndexed(pkg=0, index=2)]
    ),
    LangStrSpecValue('plain'),
]
for case in rt_cases:
    json_in = dataclass_to_json(case)
    native = babase.LangStr(json_in)
    back = dataclass_from_json(LangStrSpec, native.to_json())
    assert back == case, f'round-trip mismatch: {back} != {case}'

# Content equality + hashing.
val_a = babase.LangStr(dataclass_to_json(rt_cases[1]))
val_b = babase.LangStr(dataclass_to_json(rt_cases[1]))
val_c = babase.LangStr(dataclass_to_json(rt_cases[0]))
assert val_a == val_b and val_a is not val_b
assert val_a != val_c
assert hash(val_a) == hash(val_b)
assert len({val_a, val_b}) == 1

# Malformed input raises cleanly.
for bad in ('nope', '[]', '{"t": "x"}', '{"t": "r", "a": "y"}'):
    try:
        babase.LangStr(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f'no error for {bad!r}')

# Depth cap: the native parse rejects over-deep trees outright
# (stricter than the Python side, whose cap fires at eval time --
# wire data is untrusted, so refusing at parse is the safer posture).
deep: LangStrSpec = LangStrSpecValue('bottom')
for _i in range(17):
    deep = LangStrSpecValue('{sub}', {'sub': deep})
assert pyctx.decode(deep).startswith('LANGSTR_ERROR:')
try:
    babase.LangStr(dataclass_to_json(deep))
except ValueError:
    pass
else:
    raise AssertionError('no depth-cap error')

print('LANGSTR-PARITY-OK')
"""


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_native_lang_str_parity() -> None:
    """Native LangStrSpec parses/evaluates identically to the Python impl."""
    apprun.python_command(_PARITY_SCRIPT, purpose='langstr parity test')
