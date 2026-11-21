# Released under the MIT License. See LICENSE for details.
#
"""Testing our custom characters' two-form icon pairing.

Profile icons, flags and account/platform logos each come as a
superscript character (shown small and raised next to names) and a
full-size ``_FULL`` twin (see ``SpecialChar.full_size``). The engine
derives each superscript's glyph from its twin's, so a pairing that
is missing, one-sided or misnamed would draw nothing or the wrong art.
"""

import os
import re

from bacommon.text import SpecialChar

_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    'src',
    'ballistica',
    'base',
    'graphics',
    'text',
    'font_big_and_extras_data.h',
)


def _extras_glyph_data() -> list[list[float]]:
    with open(_DATA_PATH, encoding='utf-8') as infile:
        text = infile.read()
    start = text.index('g_glyphs_extras[')
    body = text[text.index('{', start) + 1 : text.index('};', start)]
    return [
        [float(v.strip().rstrip('f')) for v in m.group(1).split(',')]
        for m in re.finditer(r'\{([^{}]*)\}', body)
    ]


def test_pairing_is_consistent() -> None:
    """Every two-form icon pairs both ways, named X / X_FULL."""
    superscripts = [c for c in SpecialChar if c.is_superscript]
    fulls = [c for c in SpecialChar if c.full_size is c]
    assert superscripts and fulls
    for char in superscripts:
        full = char.full_size
        assert full is not None
        assert full.full_size is full, f'{full.name} not classed full-size'
        assert full.name == f'{char.name}_FULL', char.name
        assert full.superscript is char
        assert char.superscript is char
    # Each full-size twin belongs to exactly one superscript.
    twins = [c.full_size for c in superscripts]
    assert len(twins) == len(set(twins)) == len(fulls)
    # Nothing plain has a twin sitting next to it by name.
    names = {c.name for c in SpecialChar}
    for char in SpecialChar:
        if char.full_size is None:
            assert f'{char.name}_FULL' not in names, char.name
            assert not char.name.endswith('_FULL'), char.name


def test_full_size_needs_new_build() -> None:
    """Full-size twins postdate their superscripts."""
    for char in SpecialChar:
        full = char.full_size
        if full is not None and full is not char:
            assert full.min_engine_build > 0, full.name
            assert full.min_engine_build >= char.min_engine_build


def test_glyph_data() -> None:
    """Twins have tuned data; superscripts are placeholders (derived)."""
    data = _extras_glyph_data()
    for char in SpecialChar:
        index = ord(char.value) - 0xE000
        assert index < len(data), f'{char.name} not in the glyph table'
        glyph = data[index]
        if char.is_superscript:
            assert not any(glyph), (
                f'{char.name} is derived from {char.full_size}; its own'
                ' data entry should be all zeros.'
            )
        elif char.full_size is char:
            # pen x/y, advance, x/y size, tex coords.
            assert (
                glyph[2] > 0.0 and glyph[3] > 0.0 and glyph[4] > 0.0
            ), f'{char.name} has no glyph data.'
