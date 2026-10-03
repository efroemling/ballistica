# Released under the MIT License. See LICENSE for details.
#
"""Splitting delivered characters into their parts."""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterParts:
    """A character's three parts, each as its own json (None if absent).

    A character is only a delivery bundle (a cloud profile handing over
    its look whole); nothing in a scene holds one. Use each part on its
    own: ``spaz`` for a :class:`bascenev1.SpazDef`, ``icon`` for a
    :class:`bacommon.depiction.CharacterIconDepiction`, ``name`` for a
    :class:`bacommon.depiction.NameDepiction` (see :func:`name_text`
    for its plain text).
    """

    name: str | None
    icon: str | None
    spaz: str | None


def split_character(character_json: str) -> CharacterParts:
    """Split a delivered character's json into its parts.

    Unusable json (or json that isn't an object) yields no parts.
    """
    try:
        bundle = json.loads(character_json)
    except ValueError:
        return CharacterParts(None, None, None)
    if not isinstance(bundle, dict):
        return CharacterParts(None, None, None)

    def _part(key: str) -> str | None:
        part = bundle.get(key)
        if not isinstance(part, dict):
            return None
        return json.dumps(part, separators=(',', ':'))

    return CharacterParts(name=_part('n'), icon=_part('i'), spaz=_part('s'))


def name_text(name_json: str | None) -> str | None:
    """A name definition's canonical plain text (None if unusable).

    What game logic reads of a name (player names, scoreboards, logs);
    how it is drawn is the name depiction's business.
    """
    if name_json is None:
        return None
    try:
        name = json.loads(name_json)
    except ValueError:
        return None
    basic = name.get('b') if isinstance(name, dict) else None
    text = basic.get('t') if isinstance(basic, dict) else None
    return text if isinstance(text, str) and text else None
