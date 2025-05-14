# Released under the MIT License. See LICENSE for details.
#
"""Functionality for wrangling locale info."""

from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, assert_never

if TYPE_CHECKING:
    pass


class Locale(Enum):
    """A distinct grouping of language, cultural norms, etc.

    This list of locales is considered 'sacred' - we assume any values
    added here remain in use out in the wild indefinitely. If a locale
    is superseded by a newer or more specific one, the new one should be
    added and both new and old should map to the same LocaleResolved
    value.
    """

    # No strong reason to use iso codes or whatnot for these values, so
    # just using something short but easily recognizable in english.

    ENGLISH = 'eng'
    CHINESE_TRADITIONAL = 'chn_tr'
    CHINESE_SIMPLIFIED = 'chn_sim'
    PORTUGUESE_PORTUGAL = 'prtg_pr'
    PORTUGUESE_BRAZIL = 'prtg_brz'
    ARABIC = 'arabc'
    BELARUSSIAN = 'blrs'
    CROATIAN = 'croat'
    CZECH = 'czch'
    DANISH = 'dnsh'
    DUTCH = 'dtch'
    PIRATE_SPEAK = 'pirate'
    ESPERANTO = 'esprnto'
    FILIPINO = 'filp'
    FRENCH = 'frnch'
    GERMAN = 'grmn'
    GIBBERISH = 'gibber'
    GREEK = 'greek'
    HINDI = 'hndi'
    HUNGARIAN = 'hngr'
    INDONESIAN = 'indnsn'
    ITALIAN = 'italn'
    KOREAN = 'kor'
    MALAY = 'mlay'
    PERSIAN = 'pers'
    POLISH = 'pol'
    ROMANIAN = 'rom'
    RUSSIAN = 'rusn'
    SERBIAN = 'srbn'
    SPANISH_LATIN_AMERICA = 'spn_lat'
    SPANISH_SPAIN = 'spn_spn'
    SLOVAK = 'slvk'
    SWEDISH = 'swed'
    TAMIL = 'taml'
    THAI = 'thai'
    TURKISH = 'turk'
    UKRAINIAN = 'ukrn'
    VENETIAN = 'venetn'
    VIETNAMESE = 'viet'

    # Note: we cache these functions so we only have to traverse long
    # lists of if-statements once per value.

    @cached_property
    def resolved(self) -> LocaleResolved:
        """Return the associated resolved locale."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        cls = type(self)
        R = LocaleResolved

        if self is cls.ENGLISH:
            return R.ENGLISH
        if self is cls.CHINESE_TRADITIONAL:
            return R.CHINESE_TRADITIONAL
        if self is cls.CHINESE_SIMPLIFIED:
            return R.CHINESE_SIMPLIFIED
        if self is cls.PORTUGUESE_PORTUGAL:
            return R.PORTUGUESE_PORTUGAL
        if self is cls.PORTUGUESE_BRAZIL:
            return R.PORTUGUESE_BRAZIL
        if self is cls.ARABIC:
            return R.ARABIC
        if self is cls.BELARUSSIAN:
            return R.BELARUSSIAN
        if self is cls.CROATIAN:
            return R.CROATIAN
        if self is cls.CZECH:
            return R.CZECH
        if self is cls.DANISH:
            return R.DANISH
        if self is cls.DUTCH:
            return R.DUTCH
        if self is cls.PIRATE_SPEAK:
            return R.PIRATE_SPEAK
        if self is cls.ESPERANTO:
            return R.ESPERANTO
        if self is cls.FILIPINO:
            return R.FILIPINO
        if self is cls.FRENCH:
            return R.FRENCH
        if self is cls.GERMAN:
            return R.GERMAN
        if self is cls.GIBBERISH:
            return R.GIBBERISH
        if self is cls.GREEK:
            return R.GREEK
        if self is cls.HINDI:
            return R.HINDI
        if self is cls.HUNGARIAN:
            return R.HUNGARIAN
        if self is cls.INDONESIAN:
            return R.INDONESIAN
        if self is cls.ITALIAN:
            return R.ITALIAN
        if self is cls.KOREAN:
            return R.KOREAN
        if self is cls.MALAY:
            return R.MALAY
        if self is cls.PERSIAN:
            return R.PERSIAN
        if self is cls.POLISH:
            return R.POLISH
        if self is cls.ROMANIAN:
            return R.ROMANIAN
        if self is cls.RUSSIAN:
            return R.RUSSIAN
        if self is cls.SERBIAN:
            return R.SERBIAN
        if self is cls.SPANISH_LATIN_AMERICA:
            return R.SPANISH_LATIN_AMERICA
        if self is cls.SPANISH_SPAIN:
            return R.SPANISH_SPAIN
        if self is cls.SLOVAK:
            return R.SLOVAK
        if self is cls.SWEDISH:
            return R.SWEDISH
        if self is cls.TAMIL:
            return R.TAMIL
        if self is cls.THAI:
            return R.THAI
        if self is cls.TURKISH:
            return R.TURKISH
        if self is cls.UKRAINIAN:
            return R.UKRAINIAN
        if self is cls.VENETIAN:
            return R.VENETIAN
        if self is cls.VIETNAMESE:
            return R.VIETNAMESE

        # Make sure we're covering all cases.
        assert_never(self)


class LocaleResolved(Enum):
    """A resolved :class:``Locale``. Logic should always use these.

    These values should never be stored or transmitted and should always
    come from resolving a :class:``Locale``. This gives us the freedom
    to revise this list as needed to keep our actual list of implemented
    locales as trim as possible.
    """

    ENGLISH = 'eng'
    CHINESE_TRADITIONAL = 'chn_tr'
    CHINESE_SIMPLIFIED = 'chn_sim'
    PORTUGUESE_PORTUGAL = 'prtg_pr'
    PORTUGUESE_BRAZIL = 'prtg_brz'
    ARABIC = 'arabc'
    BELARUSSIAN = 'blrs'
    CROATIAN = 'croat'
    CZECH = 'czch'
    DANISH = 'dnsh'
    DUTCH = 'dtch'
    PIRATE_SPEAK = 'pirate'
    ESPERANTO = 'esprnto'
    FILIPINO = 'filp'
    FRENCH = 'frnch'
    GERMAN = 'grmn'
    GIBBERISH = 'gibber'
    GREEK = 'greek'
    HINDI = 'hndi'
    HUNGARIAN = 'hngr'
    INDONESIAN = 'indnsn'
    ITALIAN = 'italn'
    KOREAN = 'kor'
    MALAY = 'mlay'
    PERSIAN = 'pers'
    POLISH = 'pol'
    ROMANIAN = 'rom'
    RUSSIAN = 'rusn'
    SERBIAN = 'srbn'
    SPANISH_LATIN_AMERICA = 'spn_lat'
    SPANISH_SPAIN = 'spn_spn'
    SLOVAK = 'slvk'
    SWEDISH = 'swed'
    TAMIL = 'taml'
    THAI = 'thai'
    TURKISH = 'turk'
    UKRAINIAN = 'ukrn'
    VENETIAN = 'venetn'
    VIETNAMESE = 'viet'

    # Note: we cache these functions so we only have to traverse long
    # lists of if-statements once per value.

    # TODO: This call is specific to the client so should probably be
    # moved to the app's locale subsystem or whatnot.
    @cached_property
    def requires_full_unicode_display(self) -> bool:
        """Do we need to be able to draw full unicode to show this?"""
        # pylint: disable=too-many-boolean-expressions

        cls = type(self)

        # DO need full unicode.
        if (
            self is cls.CHINESE_TRADITIONAL
            or self is cls.CHINESE_SIMPLIFIED
            or self is cls.ARABIC
            or self is cls.HINDI
            or self is cls.KOREAN
            or self is cls.PERSIAN
            or self is cls.TAMIL
            or self is cls.THAI
            or self is cls.VIETNAMESE
        ):
            return True

        # Do NOT need full unicode.
        if (
            self is cls.ENGLISH
            or self is cls.PORTUGUESE_PORTUGAL
            or self is cls.PORTUGUESE_BRAZIL
            or self is cls.BELARUSSIAN
            or self is cls.CROATIAN
            or self is cls.CZECH
            or self is cls.DANISH
            or self is cls.DUTCH
            or self is cls.PIRATE_SPEAK
            or self is cls.ESPERANTO
            or self is cls.FILIPINO
            or self is cls.FRENCH
            or self is cls.GERMAN
            or self is cls.GIBBERISH
            or self is cls.GREEK
            or self is cls.HUNGARIAN
            or self is cls.INDONESIAN
            or self is cls.ITALIAN
            or self is cls.MALAY
            or self is cls.POLISH
            or self is cls.ROMANIAN
            or self is cls.RUSSIAN
            or self is cls.SERBIAN
            or self is cls.SPANISH_LATIN_AMERICA
            or self is cls.SPANISH_SPAIN
            or self is cls.SLOVAK
            or self is cls.SWEDISH
            or self is cls.TURKISH
            or self is cls.UKRAINIAN
            or self is cls.VENETIAN
        ):
            return False

        # Make sure we're covering all cases.
        assert_never(self)
