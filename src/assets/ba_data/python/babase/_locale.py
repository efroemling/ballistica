# Released under the MIT License. See LICENSE for details.
#
"""Locale related functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING, override, assert_never

from functools import cache

from bacommon.locale import Locale, LocaleResolved

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import applog

if TYPE_CHECKING:
    from typing import Any, Sequence

    import babase


class LocaleSubsystem(AppSubsystem):
    """Locale functionality for the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.locale` attr on the :class:`~babase.App` class.
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_locale: Locale | None = None

        # Calc our default locale based on the locale-tag provided by
        # the native layer.
        env = _babase.env()
        ba_locale = env.get('ba_locale')
        locale_tag = env.get('locale')
        if not isinstance(ba_locale, str) or not isinstance(locale_tag, str):
            applog.warning(
                'Seem to be running in a dummy env; using en-US locale-tag.'
            )
            ba_locale = ''
            locale_tag = 'en-US'

        #: The default locale based on the current runtime environment
        #: and app capabilities. This locale will be used unless the user
        #: explicitly overrides it.
        self.default_locale: Locale = Locale.ENGLISH

        # If a Locale long-name was provided, try to use that.
        have_valid_ba_locale = False
        if ba_locale:
            try:
                self.default_locale = Locale.from_long_value(ba_locale)
                have_valid_ba_locale = True
            except ValueError:
                applog.error(
                    'Invalid ba_locale "%s";'
                    ' will fall back to using locale tag.',
                    ba_locale,
                )

        # Otherwise calc Locale from a tag ('en-US', etc.)
        if not have_valid_ba_locale:
            self.default_locale = LocaleResolved.from_tag(locale_tag).locale

        # If we can't properly display this default locale, set it to
        # English instead.
        if not self.can_display_locale(self.default_locale):
            self.default_locale = Locale.ENGLISH

        assert self.can_display_locale(self.default_locale)

    @override
    def apply_app_config(self) -> None:
        """:meta private:"""
        assert _babase.in_logic_thread()
        assert isinstance(_babase.app.config, dict)

        locale = self.default_locale

        # Look for a 'Lang' in app-config to override the default. We
        # expect this to be a Locale long-value such as
        # 'ChineseTraditional'.
        lang = _babase.app.config.get('Lang')
        if lang is not None:
            try:
                locale = Locale.from_long_value(lang)
            except ValueError:
                applog.error(
                    'Invalid Lang "%s"; falling back to default.', lang
                )
        # Convert the locale to resolved and back again to make sure
        # we're loading a currently-supported one (for example this will
        # convert 'Spanish' to 'SpanishLatinAmerica').
        locale = locale.resolved.locale

        self._current_locale = locale

        _babase.app.lang.setlanguage(
            locale.long_value,
            print_change=False,
            store_to_config=False,
            ignore_redundant=True,
        )

    @property
    def current_locale(self) -> Locale:
        """The current locale for the app."""
        if self._current_locale is None:
            raise RuntimeError('Locale is not set.')
        return self._current_locale

    @staticmethod
    @cache
    def can_display_locale(locale: Locale) -> bool:
        """Are we able to display the passed locale?

        Some locales require integration with the OS to display the full
        range of unicode text, which is not implemented on all
        platforms.
        """
        # pylint: disable=too-many-boolean-expressions

        cls = LocaleResolved
        rlocale = locale.resolved

        # DO need full unicode.
        if (
            rlocale is cls.CHINESE_TRADITIONAL
            or rlocale is cls.CHINESE_SIMPLIFIED
            or rlocale is cls.ARABIC
            or rlocale is cls.HINDI
            or rlocale is cls.KOREAN
            or rlocale is cls.PERSIAN
            or rlocale is cls.TAMIL
            or rlocale is cls.THAI
            or rlocale is cls.VIETNAMESE
        ):
            # Return True only if we can display full unicode.
            return _babase.supports_unicode_display()

        # Do NOT need full unicode; can always display.
        if (
            rlocale is cls.ENGLISH
            or rlocale is cls.PORTUGUESE_PORTUGAL
            or rlocale is cls.PORTUGUESE_BRAZIL
            or rlocale is cls.BELARUSSIAN
            or rlocale is cls.CROATIAN
            or rlocale is cls.CZECH
            or rlocale is cls.DANISH
            or rlocale is cls.DUTCH
            or rlocale is cls.PIRATE_SPEAK
            or rlocale is cls.ESPERANTO
            or rlocale is cls.FILIPINO
            or rlocale is cls.FRENCH
            or rlocale is cls.GERMAN
            or rlocale is cls.GIBBERISH
            or rlocale is cls.GREEK
            or rlocale is cls.HUNGARIAN
            or rlocale is cls.INDONESIAN
            or rlocale is cls.ITALIAN
            or rlocale is cls.MALAY
            or rlocale is cls.POLISH
            or rlocale is cls.ROMANIAN
            or rlocale is cls.RUSSIAN
            or rlocale is cls.SERBIAN
            or rlocale is cls.SPANISH_LATIN_AMERICA
            or rlocale is cls.SPANISH_SPAIN
            or rlocale is cls.SLOVAK
            or rlocale is cls.SWEDISH
            or rlocale is cls.TURKISH
            or rlocale is cls.UKRAINIAN
            or rlocale is cls.VENETIAN
        ):
            return True

        # Make sure we're covering all cases.
        assert_never(rlocale)
