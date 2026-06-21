# Released under the MIT License. See LICENSE for details.
#
"""Locale related functionality."""

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
        raw_locale_tag = env.get('locale')
        if not isinstance(ba_locale, str) or not isinstance(
            raw_locale_tag, str
        ):
            applog.warning(
                'Seem to be running in a dummy env; using en-US locale-tag.'
            )
            ba_locale = ''
            raw_locale_tag = 'en-US'

        #: Raw locale string tag provided by the native layer. This will
        #: be something in BCP 47 form (``en-US``) or POSIX locale form
        #: (``en_US.UTF-8``). Generally you should use more well-defined
        #: values such as :attr:`current_locale` instead of this.
        self.raw_locale_tag: str = raw_locale_tag

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
            self.default_locale = LocaleResolved.from_tag(raw_locale_tag).locale

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

    def set_locale(
        self, locale: Locale, *, store_to_config: bool = True
    ) -> None:
        """Switch the active language to ``locale``.

        Resolves the target locale's asset flavors first (downloading the
        ``language/<locale>`` blob if it isn't already local, with a
        cancelable progress dialog) and commits the switch only on
        success. Runs asynchronously; on-screen text re-translates when
        the resolve completes.

        ``store_to_config`` writes the choice as an explicit ``'Lang'``
        override; pass ``False`` for the 'auto' selection (clears the
        override so the OS-default locale is followed).
        """
        assert _babase.in_logic_thread()

        # Normalize to a currently-supported resolved locale.
        locale = locale.resolved.locale
        if not self.can_display_locale(locale):
            applog.error(
                'Cannot display locale %s on this build; ignoring switch.',
                locale.name,
            )
            return
        _babase.app.create_async_task(
            self._do_set_locale(locale, store_to_config)
        )

    async def _do_set_locale(
        self, locale: Locale, store_to_config: bool
    ) -> None:
        """Resolve + commit a language switch (see :meth:`set_locale`)."""
        import asyncio

        from babase._simpledialog import SimpleDialog
        from babase._language import Lstr
        from babase._asset_packages import loaded_asset_package_apverids
        from babase._assetsubsystem import make_progress_reporter

        task = asyncio.current_task()
        dialog: SimpleDialog | None = None

        def on_cancel() -> None:
            if task is not None:
                task.cancel()

        def ensure_dialog() -> None:
            # Lazily shown only if a real download begins (an
            # already-local/warm switch stays instant, no dialog flash).
            nonlocal dialog
            if dialog is None and _babase.app.env.gui:
                dialog = SimpleDialog(
                    title=Lstr(resource='updatingText'),
                    progress=0.0,
                    button_label=Lstr(resource='cancelText'),
                    on_button=on_cancel,
                )

        def on_update(message: str, progress: float | None) -> None:
            if dialog is not None:
                dialog.update(
                    message=message,
                    progress=0.0 if progress is None else progress,
                )

        try:
            await _babase.app.assets.resolve(
                loaded_asset_package_apverids(),
                allow_downloads=True,
                language=locale,
                on_download_starting=ensure_dialog,
                on_progress=make_progress_reporter(on_update),
            )
        except asyncio.CancelledError:
            # User hit Cancel -- bow out, leave the current locale in place.
            if dialog is not None:
                dialog.dismiss()
            applog.info('Language switch to %s cancelled.', locale.long_value)
            return
        except Exception:
            # Resolve failed -- the registry + native table are unchanged
            # on failure, so just surface the error and stay put.
            applog.exception('Error switching to locale %s.', locale.name)
            if dialog is not None:
                dialog.update(
                    title=Lstr(resource='errorText'),
                    message=Lstr(
                        resource='internal.unavailableNoConnectionText'
                    ),
                    progress=None,
                    button_label=Lstr(resource='okText'),
                    on_button=dialog.dismiss,
                )
            else:
                _babase.screenmessage(
                    'Error switching language; see log.', color=(1, 0, 0)
                )
            return

        # Success: the registry + native string table are now the target
        # locale (the resolve rebuilt the table and fired the
        # language-change cascade, so on-screen text has already
        # re-translated). Commit the locale + config.
        if dialog is not None:
            dialog.dismiss()
        self._current_locale = locale
        cfg = _babase.app.config
        if store_to_config:
            cfg['Lang'] = locale.long_value
        else:
            cfg.pop('Lang', None)
        cfg.commit()
        applog.info('Switched language to %s.', locale.long_value)

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
            or rlocale is cls.JAPANESE
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
            or rlocale is cls.KAZAKH
        ):
            return True

        # Make sure we're covering all cases.
        assert_never(rlocale)
