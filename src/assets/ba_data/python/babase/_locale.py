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
        if (
            self.requires_full_unicode_display(self.default_locale.resolved)
            and not _babase.supports_unicode_display()
        ):
            self.default_locale = Locale.ENGLISH

    @override
    def do_apply_app_config(self) -> None:
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
    def requires_full_unicode_display(
        locale: LocaleResolved,
    ) -> bool:
        """Does the locale require full unicode support to display?"""
        # pylint: disable=too-many-boolean-expressions

        cls = LocaleResolved

        # DO need full unicode.
        if (
            locale is cls.CHINESE_TRADITIONAL
            or locale is cls.CHINESE_SIMPLIFIED
            or locale is cls.ARABIC
            or locale is cls.HINDI
            or locale is cls.KOREAN
            or locale is cls.PERSIAN
            or locale is cls.TAMIL
            or locale is cls.THAI
            or locale is cls.VIETNAMESE
        ):
            return True

        # Do NOT need full unicode.
        if (
            locale is cls.ENGLISH
            or locale is cls.PORTUGUESE_PORTUGAL
            or locale is cls.PORTUGUESE_BRAZIL
            or locale is cls.BELARUSSIAN
            or locale is cls.CROATIAN
            or locale is cls.CZECH
            or locale is cls.DANISH
            or locale is cls.DUTCH
            or locale is cls.PIRATE_SPEAK
            or locale is cls.ESPERANTO
            or locale is cls.FILIPINO
            or locale is cls.FRENCH
            or locale is cls.GERMAN
            or locale is cls.GIBBERISH
            or locale is cls.GREEK
            or locale is cls.HUNGARIAN
            or locale is cls.INDONESIAN
            or locale is cls.ITALIAN
            or locale is cls.MALAY
            or locale is cls.POLISH
            or locale is cls.ROMANIAN
            or locale is cls.RUSSIAN
            or locale is cls.SERBIAN
            or locale is cls.SPANISH_LATIN_AMERICA
            or locale is cls.SPANISH_SPAIN
            or locale is cls.SLOVAK
            or locale is cls.SWEDISH
            or locale is cls.TURKISH
            or locale is cls.UKRAINIAN
            or locale is cls.VENETIAN
        ):
            return False

        # Make sure we're covering all cases.
        assert_never(locale)
