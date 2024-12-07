# Released under the MIT License. See LICENSE for details.
#
"""Defines a default keyboards."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Iterable


def split(chars: Iterable[str], maxlen: int) -> list[list[str]]:
    """Returns char groups with a fixed number of elements"""
    result = []
    shatter: list[str] = []
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


def generate_emojis(maxlen: int) -> list[list[str]]:
    """Generates a lot of UTF8 emojis prepared for bui.Keyboard pages"""
    all_emojis = split([chr(i) for i in range(0x1F601, 0x1F650)], maxlen)
    all_emojis += split([chr(i) for i in range(0x2702, 0x27B1)], maxlen)
    all_emojis += split([chr(i) for i in range(0x1F680, 0x1F6C1)], maxlen)
    return all_emojis


# ba_meta export bauiv1.Keyboard
class EnglishKeyboard(bui.Keyboard):
    """Default English keyboard."""

    name = 'English'
    chars = [
        ('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'),
        ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'),
        ('z', 'x', 'c', 'v', 'b', 'n', 'm'),
    ]
    nums = (
        '1',
        '2',
        '3',
        '4',
        '5',
        '6',
        '7',
        '8',
        '9',
        '0',
        '-',
        '/',
        ':',
        ';',
        '(',
        ')',
        '$',
        '&',
        '@',
        '"',
        '.',
        ',',
        '?',
        '!',
        '\'',
        '_',
    )
    pages: dict[str, tuple[str, ...]] = {
        f'emoji{i}': tuple(page)
        for i, page in enumerate(generate_emojis(len(nums)))
    }
