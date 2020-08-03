# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Defines a default keyboards."""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Iterable, List, Tuple, Dict


def split(chars: Iterable[str], maxlen: int) -> List[List[str]]:
    """Returns char groups with a fixed number of elements"""
    result = []
    shatter: List[str] = []
    for i in chars:
        if len(shatter) < maxlen:
            shatter.append(i)
        else:
            result.append(shatter)
            shatter = [i]
    if shatter:
        while len(shatter) < maxlen:
            shatter.append('')
        result.append(shatter)
    return result


def generate_emojis(maxlen: int) -> List[List[str]]:
    """Generates a lot of UTF8 emojis prepared for ba.Keyboard pages"""
    all_emojis = split([chr(i) for i in range(0x1F601, 0x1F650)], maxlen)
    all_emojis += split([chr(i) for i in range(0x2702, 0x27B1)], maxlen)
    all_emojis += split([chr(i) for i in range(0x1F680, 0x1F6C1)], maxlen)
    return all_emojis


# ba_meta export keyboard
class EnglishKeyboard(ba.Keyboard):
    """Default English keyboard."""
    name = 'English'
    chars = [('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'),
             ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'),
             ('z', 'x', 'c', 'v', 'b', 'n', 'm')]
    nums = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '/', ':',
            ';', '(', ')', '$', '&', '@', '"', '.', ',', '?', '!', '\'', '_')
    pages: Dict[str, Tuple[str, ...]] = {
        f'emoji{i}': tuple(page)
        for i, page in enumerate(generate_emojis(len(nums)))
    }
