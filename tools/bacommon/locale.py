# Released under the MIT License. See LICENSE for details.
#
"""Functionality for wrangling locale info."""

from __future__ import annotations

import logging
from enum import Enum
from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, assert_never, assert_type

if TYPE_CHECKING:
    pass


class Locale(Enum):
    """A distinct grouping of language, cultural norms, etc.

    This list of locales is considered 'sacred' - we assume any values
    (and associated long values) added here remain in use out in the
    wild indefinitely. If a locale is superseded by a newer or more
    specific one, the new locale should be added and both new and old
    should map to the same :class:`LocaleResolved`.
    """

    # Locale values are not iso codes or anything specific; just
    # abbreviated English strings intended to be recognizable. In cases
    # where space is unimportant or humans might be writing these, go
    # with long-values which .

    ENGLISH = 'eng'
    CHINESE = 'chn'  # Obsolete
    CHINESE_TRADITIONAL = 'chn_tr'
    CHINESE_SIMPLIFIED = 'chn_sim'
    PORTUGUESE = 'prtg'  # Obsolete
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
    SPANISH = 'spn'  # Obsolete
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

    # Note: We use if-statement chains here so we can use assert_never()
    # to ensure we cover all existing values. But we cache lookups so
    # that we only have to go through those long if-statement chains
    # once per enum value.

    @cached_property
    def long_value(self) -> str:
        """A longer more human readable alternative to value.

        Like the regular enum values, these values will never change and
        can be used for persistent storage/etc.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        cls = type(self)

        if self is cls.ENGLISH:
            return 'English'
        if self is cls.CHINESE:
            return 'Chinese'
        if self is cls.CHINESE_TRADITIONAL:
            return 'ChineseTraditional'
        if self is cls.CHINESE_SIMPLIFIED:
            return 'ChineseSimplified'
        if self is cls.PORTUGUESE:
            return 'Portuguese'
        if self is cls.PORTUGUESE_PORTUGAL:
            return 'PortuguesePortugal'
        if self is cls.PORTUGUESE_BRAZIL:
            return 'PortugueseBrazil'
        if self is cls.ARABIC:
            return 'Arabic'
        if self is cls.BELARUSSIAN:
            return 'Belarussian'
        if self is cls.CROATIAN:
            return 'Croatian'
        if self is cls.CZECH:
            return 'Czech'
        if self is cls.DANISH:
            return 'Danish'
        if self is cls.DUTCH:
            return 'Dutch'
        if self is cls.PIRATE_SPEAK:
            return 'PirateSpeak'
        if self is cls.ESPERANTO:
            return 'Esperanto'
        if self is cls.FILIPINO:
            return 'Filipino'
        if self is cls.FRENCH:
            return 'French'
        if self is cls.GERMAN:
            return 'German'
        if self is cls.GIBBERISH:
            return 'Gibberish'
        if self is cls.GREEK:
            return 'Greek'
        if self is cls.HINDI:
            return 'Hindi'
        if self is cls.HUNGARIAN:
            return 'Hungarian'
        if self is cls.INDONESIAN:
            return 'Indonesian'
        if self is cls.ITALIAN:
            return 'Italian'
        if self is cls.KOREAN:
            return 'Korean'
        if self is cls.MALAY:
            return 'Malay'
        if self is cls.PERSIAN:
            return 'Persian'
        if self is cls.POLISH:
            return 'Polish'
        if self is cls.ROMANIAN:
            return 'Romanian'
        if self is cls.RUSSIAN:
            return 'Russian'
        if self is cls.SERBIAN:
            return 'Serbian'
        if self is cls.SPANISH:
            return 'Spanish'
        if self is cls.SPANISH_LATIN_AMERICA:
            return 'SpanishLatinAmerica'
        if self is cls.SPANISH_SPAIN:
            return 'SpanishSpain'
        if self is cls.SLOVAK:
            return 'Slovak'
        if self is cls.SWEDISH:
            return 'Swedish'
        if self is cls.TAMIL:
            return 'Tamil'
        if self is cls.THAI:
            return 'Thai'
        if self is cls.TURKISH:
            return 'Turkish'
        if self is cls.UKRAINIAN:
            return 'Ukrainian'
        if self is cls.VENETIAN:
            return 'Venetian'
        if self is cls.VIETNAMESE:
            return 'Vietnamese'

        # Make sure we've covered all cases.
        assert_never(self)

    @classmethod
    def from_long_value(cls, value: str) -> Locale:
        """Given a long value, return a Locale."""

        # Build a map of long-values to locales on demand.
        storekey = '_from_long_value'
        fromvals: dict[str, Locale] | None = getattr(cls, storekey, None)
        if fromvals is None:
            fromvals = {val.long_value: val for val in cls}
            setattr(cls, storekey, fromvals)

        try:
            return fromvals[value]
        except KeyError as exc:
            raise ValueError(f'Invalid long value "{value}"') from exc

    @cached_property
    def description(self) -> str:
        """A human readable description for the locale.

        Intended as instructions to humans or AI for translating. For
        most locales this is simply the language name, but for special
        ones like pirate-speak it may include instructions.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        cls = type(self)

        if self is cls.ENGLISH:
            return 'English'
        if self is cls.CHINESE:
            return 'Chinese'
        if self is cls.CHINESE_TRADITIONAL:
            return 'Chinese (Traditional)'
        if self is cls.CHINESE_SIMPLIFIED:
            return 'Chinese (Simplified)'
        if self is cls.PORTUGUESE:
            return 'Portuguese'
        if self is cls.PORTUGUESE_PORTUGAL:
            return 'Portuguese (Portugal)'
        if self is cls.PORTUGUESE_BRAZIL:
            return 'Portuguese (Brazil)'
        if self is cls.ARABIC:
            return 'Arabic'
        if self is cls.BELARUSSIAN:
            return 'Belarussian'
        if self is cls.CROATIAN:
            return 'Croatian'
        if self is cls.CZECH:
            return 'Czech'
        if self is cls.DANISH:
            return 'Danish'
        if self is cls.DUTCH:
            return 'Dutch'
        if self is cls.PIRATE_SPEAK:
            return 'Pirate-Speak (English as spoken by a pirate)'
        if self is cls.ESPERANTO:
            return 'Esperanto'
        if self is cls.FILIPINO:
            return 'Filipino'
        if self is cls.FRENCH:
            return 'French'
        if self is cls.GERMAN:
            return 'German'
        if self is cls.GIBBERISH:
            return (
                'Gibberish (imaginary words vaguely' ' reminiscent of English)'
            )
        if self is cls.GREEK:
            return 'Greek'
        if self is cls.HINDI:
            return 'Hindi'
        if self is cls.HUNGARIAN:
            return 'Hungarian'
        if self is cls.INDONESIAN:
            return 'Indonesian'
        if self is cls.ITALIAN:
            return 'Italian'
        if self is cls.KOREAN:
            return 'Korean'
        if self is cls.MALAY:
            return 'Malay'
        if self is cls.PERSIAN:
            return 'Persian'
        if self is cls.POLISH:
            return 'Polish'
        if self is cls.ROMANIAN:
            return 'Romanian'
        if self is cls.RUSSIAN:
            return 'Russian'
        if self is cls.SERBIAN:
            return 'Serbian'
        if self is cls.SPANISH:
            return 'Spanish'
        if self is cls.SPANISH_LATIN_AMERICA:
            return 'Spanish (Latin America)'
        if self is cls.SPANISH_SPAIN:
            return 'Spanish (Spain)'
        if self is cls.SLOVAK:
            return 'Slovak'
        if self is cls.SWEDISH:
            return 'Swedish'
        if self is cls.TAMIL:
            return 'Tamil'
        if self is cls.THAI:
            return 'Thai'
        if self is cls.TURKISH:
            return 'Turkish'
        if self is cls.UKRAINIAN:
            return 'Ukrainian'
        if self is cls.VENETIAN:
            return 'Venetian'
        if self is cls.VIETNAMESE:
            return 'Vietnamese'

        # Make sure we've covered all cases.
        assert_never(self)

    @cached_property
    def resolved(self) -> LocaleResolved:
        """Return the associated resolved locale."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        cls = type(self)
        R = LocaleResolved

        if self is cls.ENGLISH:
            return R.ENGLISH
        if self is cls.CHINESE_SIMPLIFIED or self is cls.CHINESE:
            return R.CHINESE_SIMPLIFIED
        if self is cls.CHINESE_TRADITIONAL:
            return R.CHINESE_TRADITIONAL
        if self is cls.PORTUGUESE_BRAZIL or self is cls.PORTUGUESE:
            return R.PORTUGUESE_BRAZIL
        if self is cls.PORTUGUESE_PORTUGAL:
            return R.PORTUGUESE_PORTUGAL
        if self is cls.SPANISH_LATIN_AMERICA or self is cls.SPANISH:
            return R.SPANISH_LATIN_AMERICA
        if self is cls.SPANISH_SPAIN:
            return R.SPANISH_SPAIN
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
    """A resolved :class:`Locale` for use in logic.

    These values should never be stored or transmitted and should always
    come from resolving a :class:`Locale` which *can* be
    stored/transmitted. This gives us the freedom to revise this list as
    needed to keep our actual list of implemented resolved-locales as
    trim as possible.
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

    # Note: We use if-statement chains here so we can use assert_never()
    # to ensure we cover all existing values. But we cache lookups so
    # that we only have to go through those long if-statement chains
    # once per enum value.

    @cached_property
    def locale(self) -> Locale:
        """Return a locale that resolves to this resolved locale.

        In some cases, such as when presenting locale options to the
        user, it makes sense to iterate over resolved locale values, as
        regular locales may include obsolete or redundant values. When
        storing locale values to disk or transmitting them, however, it
        is important to use plain locales. This method can be used to
        get back to a plain locale from a resolved one.
        """
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        cls = type(self)

        if self is cls.ENGLISH:
            return Locale.ENGLISH
        if self is cls.CHINESE_TRADITIONAL:
            return Locale.CHINESE_TRADITIONAL
        if self is cls.CHINESE_SIMPLIFIED:
            return Locale.CHINESE_SIMPLIFIED
        if self is cls.PORTUGUESE_PORTUGAL:
            return Locale.PORTUGUESE_PORTUGAL
        if self is cls.PORTUGUESE_BRAZIL:
            return Locale.PORTUGUESE_BRAZIL
        if self is cls.ARABIC:
            return Locale.ARABIC
        if self is cls.BELARUSSIAN:
            return Locale.BELARUSSIAN
        if self is cls.CROATIAN:
            return Locale.CROATIAN
        if self is cls.CZECH:
            return Locale.CZECH
        if self is cls.DANISH:
            return Locale.DANISH
        if self is cls.DUTCH:
            return Locale.DUTCH
        if self is cls.PIRATE_SPEAK:
            return Locale.PIRATE_SPEAK
        if self is cls.ESPERANTO:
            return Locale.ESPERANTO
        if self is cls.FILIPINO:
            return Locale.FILIPINO
        if self is cls.FRENCH:
            return Locale.FRENCH
        if self is cls.GERMAN:
            return Locale.GERMAN
        if self is cls.GIBBERISH:
            return Locale.GIBBERISH
        if self is cls.GREEK:
            return Locale.GREEK
        if self is cls.HINDI:
            return Locale.HINDI
        if self is cls.HUNGARIAN:
            return Locale.HUNGARIAN
        if self is cls.INDONESIAN:
            return Locale.INDONESIAN
        if self is cls.ITALIAN:
            return Locale.ITALIAN
        if self is cls.KOREAN:
            return Locale.KOREAN
        if self is cls.MALAY:
            return Locale.MALAY
        if self is cls.PERSIAN:
            return Locale.PERSIAN
        if self is cls.POLISH:
            return Locale.POLISH
        if self is cls.ROMANIAN:
            return Locale.ROMANIAN
        if self is cls.RUSSIAN:
            return Locale.RUSSIAN
        if self is cls.SERBIAN:
            return Locale.SERBIAN
        if self is cls.SPANISH_LATIN_AMERICA:
            return Locale.SPANISH_LATIN_AMERICA
        if self is cls.SPANISH_SPAIN:
            return Locale.SPANISH_SPAIN
        if self is cls.SLOVAK:
            return Locale.SLOVAK
        if self is cls.SWEDISH:
            return Locale.SWEDISH
        if self is cls.TAMIL:
            return Locale.TAMIL
        if self is cls.THAI:
            return Locale.THAI
        if self is cls.TURKISH:
            return Locale.TURKISH
        if self is cls.UKRAINIAN:
            return Locale.UKRAINIAN
        if self is cls.VENETIAN:
            return Locale.VENETIAN
        if self is cls.VIETNAMESE:
            return Locale.VIETNAMESE

        # Make sure we're covering all cases.
        assert_never(self)

    @cached_property
    def tag(self) -> str:
        """An IETF BCP 47 tag for this locale.

        This is often simply a language code ('en') but may in some
        cases include the country ('pt-BR') or script ('zh-Hans').
        Locales which are not "real" will include an 'x' in the middle
        ('en-x-pirate').
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        cls = type(self)

        val: str | None = None

        if self is cls.ENGLISH:
            val = 'en'
        elif self is cls.CHINESE_TRADITIONAL:
            val = 'zh-Hant'
        elif self is cls.CHINESE_SIMPLIFIED:
            val = 'zh-Hans'
        elif self is cls.PORTUGUESE_PORTUGAL:
            val = 'pt-PT'
        elif self is cls.PORTUGUESE_BRAZIL:
            val = 'pt-BR'
        elif self is cls.ARABIC:
            val = 'ar'
        elif self is cls.BELARUSSIAN:
            val = 'be'
        elif self is cls.CROATIAN:
            val = 'hr'
        elif self is cls.CZECH:
            val = 'cs'
        elif self is cls.DANISH:
            val = 'da'
        elif self is cls.DUTCH:
            val = 'nl'
        elif self is cls.PIRATE_SPEAK:
            # 'x' in BCP 47 denotes private-use values.
            val = 'en-x-pirate'
        elif self is cls.ESPERANTO:
            val = 'eo'
        elif self is cls.FILIPINO:
            val = 'fil'
        elif self is cls.FRENCH:
            val = 'fr'
        elif self is cls.GERMAN:
            val = 'de'
        elif self is cls.GIBBERISH:
            # 'x' in BCP 47 denotes private-use values.
            val = 'en-x-gibberish'
        elif self is cls.GREEK:
            val = 'el'
        elif self is cls.HINDI:
            val = 'hi'
        elif self is cls.HUNGARIAN:
            val = 'hu'
        elif self is cls.INDONESIAN:
            val = 'id'
        elif self is cls.ITALIAN:
            val = 'it'
        elif self is cls.KOREAN:
            val = 'ko'
        elif self is cls.MALAY:
            val = 'ms'
        elif self is cls.PERSIAN:
            val = 'fa'
        elif self is cls.POLISH:
            val = 'pl'
        elif self is cls.ROMANIAN:
            val = 'ro'
        elif self is cls.RUSSIAN:
            val = 'ru'
        elif self is cls.SERBIAN:
            val = 'sr'
        elif self is cls.SPANISH_LATIN_AMERICA:
            val = 'es-419'
        elif self is cls.SPANISH_SPAIN:
            val = 'es-ES'
        elif self is cls.SLOVAK:
            val = 'sk'
        elif self is cls.SWEDISH:
            val = 'sv'
        elif self is cls.TAMIL:
            val = 'ta'
        elif self is cls.THAI:
            val = 'th'
        elif self is cls.TURKISH:
            val = 'tr'
        elif self is cls.UKRAINIAN:
            val = 'uk'
        elif self is cls.VENETIAN:
            val = 'vec'
        elif self is cls.VIETNAMESE:
            val = 'vi'
        else:
            # Make sure we cover all cases.
            assert_never(self)

        assert_type(val, str)

        # Sanity check: the tag we return should lead back to us if we
        # use it to get a Locale and then resolve that Locale. Make some
        # noise if not so we can fix it.
        lrcheck = LocaleResolved.from_tag(val)
        if lrcheck is not self:
            logging.warning(
                'LocaleResolved.from_tag().resolved for "%s" yielded %s;'
                ' expected %s.',
                val,
                lrcheck.name,
                self.name,
            )

        return val

    @classmethod
    @lru_cache(maxsize=128)
    def from_tag(cls, tag: str) -> LocaleResolved:
        """Return a locale for a given string tag.

        Tags can be provided in BCP 47 form ('en-US') or POSIX locale
        string form ('en_US.UTF-8').
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-return-statements

        # POSIX locale strings can contain a dot followed by an
        # encoding. Strip that off.
        tag2 = tag.split('.')[0]

        # Normalize things to lowercase and underscores (we should see
        # 'zh_HANT' and 'zh-Hant' as the same).
        bits = [bit.lower() for bit in tag2.replace('-', '_').split('_')]

        if not bits or not bits[0]:
            raise ValueError(f'Invalid tag "{tag}".')

        lang = bits[0]
        extras = bits[1:]

        if lang == 'en':
            if 'x' in extras and 'pirate' in extras:
                return cls.PIRATE_SPEAK
            if 'x' in extras and 'gibberish' in extras:
                return cls.GIBBERISH
            return cls.ENGLISH
        if lang == 'zh':
            # With no extras, default to simplified.
            if not extras or any(val in extras for val in ['hans', 'cn', 'sg']):
                return cls.CHINESE_SIMPLIFIED
            if any(val in extras for val in ['hant', 'tw']):
                return cls.CHINESE_TRADITIONAL

            # Make noise if we come across something unexpected so we
            # can add it.
            fallback = cls.CHINESE_SIMPLIFIED
            logging.warning(
                '%s: Unknown Chinese tag variant "%s"; returning %s.',
                cls.__name__,
                tag,
                fallback.name,
            )
            return fallback
        if lang == 'pt':
            # With no extras, default to Brazil.
            if not extras or 'br' in extras:
                return cls.PORTUGUESE_BRAZIL
            if any(
                val in extras
                for val in ['pt', 'ao', 'mz', 'tl', 'cv', 'gw', 'st']
            ):
                return cls.PORTUGUESE_PORTUGAL

            # Make noise if we come across something unexpected so we
            # can add it.
            fallback = cls.PORTUGUESE_BRAZIL
            logging.warning(
                '%s: Unknown Portuguese tag variant "%s"; returning %s.',
                cls.__name__,
                tag,
                fallback.name,
            )
            return fallback
        if lang == 'es':
            # With no extras, default to latin-america spanish.
            if not extras or any(
                val in extras
                for val in [
                    '419',  # Latin America / Carribean region
                    'mx',  # Mexico
                    'ar',  # Argentina
                    'co',  # Colombia
                    'cl',  # Chile
                    'pe',  # Peru
                    've',  # Venezuela
                    'cr',  # Costa Rica
                    'pr',  # Puerto Rico
                    'do',  # Dominican Republic
                    'uy',  # Uruguay
                    'ec',  # Ecuador
                    'pa',  # Panama
                    'bo',  # Bolivia
                ]
            ):
                return cls.SPANISH_LATIN_AMERICA
            if 'es' in extras:
                return cls.SPANISH_SPAIN

            # Make noise if we come across something unexpected so we
            # can add it.
            fallback = cls.SPANISH_LATIN_AMERICA
            logging.warning(
                '%s: Unknown Spanish tag variant "%s"; returning %s.',
                cls.__name__,
                tag,
                fallback.name,
            )
            return fallback
        if lang == 'c':
            # The C.UTF-8 is a minimal locale defined by POSIX we
            # sometimes run into.
            return cls.ENGLISH
        if lang == 'ar':
            return cls.ARABIC
        if lang == 'be':
            return cls.BELARUSSIAN
        if lang == 'hr':
            return cls.CROATIAN
        if lang == 'cs':
            return cls.CZECH
        if lang == 'da':
            return cls.DANISH
        if lang == 'nl':
            return cls.DUTCH
        if lang == 'eo':
            return cls.ESPERANTO
        if lang == 'fil':
            return cls.FILIPINO
        if lang == 'fr':
            return cls.FRENCH
        if lang == 'de':
            return cls.GERMAN
        if lang == 'el':
            return cls.GREEK
        if lang == 'hi':
            return cls.HINDI
        if lang == 'hu':
            return cls.HUNGARIAN
        if lang == 'id':
            return cls.INDONESIAN
        if lang == 'it':
            return cls.ITALIAN
        if lang == 'ko':
            return cls.KOREAN
        if lang == 'ms':
            return cls.MALAY
        if lang == 'fa':
            return cls.PERSIAN
        if lang == 'pl':
            return cls.POLISH
        if lang == 'ro':
            return cls.ROMANIAN
        if lang == 'ru':
            return cls.RUSSIAN
        if lang == 'sr':
            return cls.SERBIAN
        if lang == 'sk':
            return cls.SLOVAK
        if lang == 'sv':
            return cls.SWEDISH
        if lang == 'ta':
            return cls.TAMIL
        if lang == 'th':
            return cls.THAI
        if lang == 'tr':
            return cls.TURKISH
        if lang == 'uk':
            return cls.UKRAINIAN
        if lang == 'vec':
            return cls.VENETIAN
        if lang == 'vi':
            return cls.VIETNAMESE

        # Make noise if we come across something unexpected so we can
        # add it.
        fallback = cls.ENGLISH
        logging.warning(
            '%s: Unknown tag "%s"; returning %s.',
            cls.__name__,
            tag,
            fallback.name,
        )
        return fallback
