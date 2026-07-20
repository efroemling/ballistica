# Released under the MIT License. See LICENSE for details.
#
"""Language related functionality."""

import json
from functools import partial
from typing import TYPE_CHECKING, overload, override

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import applog

if TYPE_CHECKING:
    from typing import Any, Sequence

    import babase


#: Process-lifetime cache for :func:`get_legacy_langdata` (the constant
#: ``legacylangdata`` blob is flavor-invariant, so it is stable for
#: the life of the process once read).
_g_legacy_langdata: dict[str, Any] | None = None


def get_legacy_langdata() -> dict[str, Any]:
    """Return the parsed legacy language-data blob (cached process-wide).

    This is the legacy ``langdata.json`` payload (translated language
    names + translation contributors), now sourced from the builtin
    asset-package's flavor-invariant ``constant`` bucket (logical path
    ``legacylangdata``) rather than a bundled data file.

    Returns ``{}`` when the blob is unavailable (headless / no bundled
    asset-package manifest / not yet resolved) or on any read error, so
    callers can ``.get(...)`` safely.
    """
    global _g_legacy_langdata  # pylint: disable=global-statement
    if _g_legacy_langdata is not None:
        return _g_legacy_langdata

    # Imported lazily to avoid a module-load cycle (asset-packages pulls
    # in babase bits that aren't ready at _language import time).
    from babase._asset_packages import loaded_asset_package_apverids

    # The langdata rides whichever builtin package introduced it
    # (babuiltinassets today); probe each bundled package and take the
    # first that carries it rather than hard-coding the package name.
    result: dict[str, Any] = {}
    for apverid in loaded_asset_package_apverids():
        path = _babase.get_asset_package_constant_blob_path(
            apverid, 'legacylangdata'
        )
        if path is None:
            continue
        try:
            with open(path, encoding='utf-8') as infile:
                result = json.loads(infile.read())
        except Exception:
            # Don't cache a transient read failure; a later call (after a
            # successful resolve) can still succeed.
            applog.exception('Error reading legacy langdata from %s.', path)
            return {}
        break

    _g_legacy_langdata = result
    return result


class LanguageSubsystem(AppSubsystem):
    """Legacy language functionality for the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.lang` attr on the :class:`~babase.App` class.

    .. deprecated:: 1.7.40

       Use :class:`~babase.LocaleSubsystem` for language/locale
       functionality when possible. This old class remains for
       compatibility and will be removed eventually.
    """

    def __init__(self) -> None:
        super().__init__()
        self._language: str | None = None
        self._test_timer: babase.AppTimer | None = None

    @property
    def locale(self) -> str:
        """Raw country/language code detected by the game (such as "en_US").

        Generally for language-specific code you should look at
        :attr:`language`, which is the language the game is using (which
        may differ from locale if the user sets a language, etc.)
        """
        env = _babase.env()
        locale = env.get('locale')
        if not isinstance(locale, str):
            applog.warning(
                'Seem to be running in a dummy env; returning en_US locale.'
            )
            locale = 'en_US'
        return locale

    @property
    def language(self) -> str:
        """The current active language for the app.

        This can be selected explicitly by the user or may be set
        automatically based on locale or other factors.
        """
        if self._language is None:
            raise RuntimeError('App language is not yet set.')

        return self._language

    def testlanguage(self, langid: str) -> None:
        """Set the app to test an in-progress language.

        Pass a language id from the translation editor website as 'langid';
        something like 'Gibberish_3263'. Once set to testing, the engine
        will repeatedly download and apply that same test language, so
        changes can be made to it and observed live.
        """
        print(
            f'Language test mode enabled.'
            f' Will fetch and apply \'{langid}\' every 5 seconds,'
            f' so you can see your changes live.'
        )
        self._test_timer = _babase.AppTimer(
            5.0, partial(self._update_test_language, langid), repeat=True
        )
        self._update_test_language(langid)

    def _on_test_lang_response(
        self, langid: str, response: None | dict[str, Any]
    ) -> None:
        if response is None:
            return
        self.setlanguage(response)
        print(f'Fetched and applied {langid}.')

    def _update_test_language(self, langid: str) -> None:
        if _babase.app.classic is None:
            raise RuntimeError('This requires classic.')

        # Only do this during normal running operation.
        appstate = _babase.app.state
        if appstate is not type(appstate).RUNNING:
            return

        _babase.app.classic.master_server_v1_get(
            'bsLangGet',
            {'lang': langid, 'format': 'json'},
            partial(self._on_test_lang_response, langid),
        )

    def setlanguage(
        self,
        language: str | dict,
        *,
        print_change: bool = True,
        store_to_config: bool = True,
        ignore_redundant: bool = False,
    ) -> None:
        """Set the active app language.

        Note that this only applies to the legacy language system and
        should not be used directly these days.
        """

        assert _babase.in_logic_thread()

        # Custom-dict injection (the old live translation-preview path) is
        # not supported by the native string table; testlanguage() is
        # deferred to the strings-asset-migration authoring work.
        if isinstance(language, dict):
            raise NotImplementedError(
                'setlanguage() with a custom dict is not supported by the'
                ' native string system (testlanguage is deferred).'
            )

        cfg = _babase.app.config
        cur_language = cfg.get('Lang', None)

        if ignore_redundant and language == self._language:
            return

        # Store this in the config if its changing.
        switched = False
        if language != cur_language and store_to_config:
            cfg['Lang'] = language
            cfg.commit()
            switched = True

        self._language = language

        # (Re)build the native string table from the bundled/resolved
        # language asset-package buckets. English is the bundled fallback
        # flavor, so this currently always yields English (strings
        # migration Step A); switching to other locales lands in Step B.
        from babase._asset_packages import loaded_asset_package_apverids

        plural_locale = _babase.app.locale.current_locale.resolved.locale.value
        _babase.reload_language(loaded_asset_package_apverids(), plural_locale)

        if switched and print_change:
            _babase.screenmessage(
                Lstr(
                    resource='languageSetText',
                    subs=[
                        ('${LANGUAGE}', Lstr(translate=('languages', language)))
                    ],
                ),
                color=(0, 1, 0),
            )

    def get_resource(
        self,
        resource: str,
        fallback_resource: str | None = None,
        fallback_value: Any = None,
    ) -> Any:
        """Return a translation resource by name.

        .. warning::

          Use :class:`~babase.Lstr` instead of this function whenever
          possible, as it will gracefully handle displaying correctly
          across multiple clients in multiple languages simultaneously.
        """
        # If we have no language set yet, set it to english (and make a
        # fuss, since we should avoid this).
        if self._language is None:
            if _babase.do_once():
                applog.warning(
                    'get_resource() called before language set;'
                    ' falling back to english.'
                )
            self.setlanguage(
                'English', print_change=False, store_to_config=False
            )

        # Resolve natively against the string table (trying
        # fallback_resource on a miss).
        val = _babase.get_resource(resource, fallback_resource)
        if val is not None:
            return val
        if fallback_value is not None:
            return fallback_value
        from babase import _error

        raise _error.NotFoundError(f"Resource not found: '{resource}'")

    def translate(
        self,
        category: str,
        strval: str,
        raise_exceptions: bool = False,
        print_errors: bool = False,
    ) -> str:
        """Translate a value (or return the value if no translation available).

        .. warning::

          Use :class:`~babase.Lstr` instead of this function whenever
          possible, as it will gracefully handle displaying correctly
          across multiple clients in multiple languages simultaneously.
        """
        # The native path never errors -- a missing translation simply
        # returns the passed value (the legacy null-means-use-value rule),
        # so the old raise_exceptions/print_errors knobs are moot.
        del raise_exceptions, print_errors
        return _babase.translate(category, strval)

    def has_resource(self, resource: str) -> bool:
        """Return whether a resource exists (by full dot-path key)."""
        return _babase.get_resource(resource) is not None

    def is_custom_unicode_char(self, char: str) -> bool:
        """Return whether a char is in the custom unicode range we use."""
        assert isinstance(char, str)
        if len(char) != 1:
            raise ValueError('Invalid Input; must be length 1')
        return 0xE000 <= ord(char) <= 0xF8FF


class Lstr:
    """Used to define strings in a language-independent way.

    These should be used whenever possible in place of hard-coded
    strings so that in-game or UI elements show up correctly on all
    clients in their currently active language.

    To see available resource keys, see the translation pages at
    `legacy.ballistica.net/translate
    <https://legacy.ballistica.net/translate>`_.

    Args:

      resource:
        Pass a string to look up a translation by resource key.

      translate:
        Pass a tuple consisting of a translation category and
        untranslated value. Any matching translation found in that
        category will be used. Otherwise the untranslated value will
        be.

      value:
        Pass a regular string value to be used as-is.

      subs:
        A sequence of 2-member tuples consisting of values and
        replacements. Replacements can be regular strings or other ``Lstr``
        values.

      fallback_resource:
        A resource key that will be used if the main one is not present for
        the current language instead of falling back to the english value
        ('resource' mode only).

      fallback_value:
        A regular string that will be used if neither the resource nor the
        fallback resource is found ('resource' mode only).


    **Example 1: Resource path** ::

        mynode.text = babase.Lstr(resource='audioSettingsWindow.titleText')

    **Example 2: Translation**

    If a translated value is available, it will be used; otherwise the
    English value will be. To see available translation categories, look
    under the ``translations`` resource section. ::

        mynode.text = babase.Lstr(translate=('gameDescriptions',
                                             'Defeat all enemies'))

    **Example 3: Substitutions**

    Substitutions can be used with ``resource`` and ``translate`` modes
    as well as the ``value`` shown here. ::

        mynode.text = babase.Lstr(value='${A} / ${B}',
                                  subs=[('${A}', str(score)),
                                        ('${B}', str(total))])

    **Example 4: Nesting**

    ``Lstr`` instances can be nested. This example would display
    the translated resource at ``'res_a'`` but replace any instances of
    ``'${NAME}'`` it contains with the translated resource at ``'res_b'``. ::

        mytextnode.text = babase.Lstr(
            resource='res_a',
            subs=[('${NAME}', babase.Lstr(resource='res_b'))])
    """

    # This class is used a lot in UI stuff and doesn't need to be
    # flexible, so let's optimize its performance a bit.
    __slots__ = ['args']

    @overload
    def __init__(
        self,
        *,
        resource: str,
        fallback_resource: str = '',
        fallback_value: str = '',
        subs: Sequence[tuple[str, str | Lstr]] | None = None,
    ) -> None:
        """Create an Lstr from a string resource."""

    @overload
    def __init__(
        self,
        *,
        translate: tuple[str, str],
        subs: Sequence[tuple[str, str | Lstr]] | None = None,
    ) -> None:
        """Create an Lstr by translating a string in a category."""

    @overload
    def __init__(
        self,
        *,
        value: str,
        subs: Sequence[tuple[str, str | Lstr]] | None = None,
    ) -> None:
        """Create an Lstr from a raw string value."""

    def __init__(self, *args: Any, **keywds: Any) -> None:
        if args:
            raise TypeError('Lstr accepts only keyword arguments')

        #: Basically just stores the exact args passed. However if Lstr
        #: values were passed for subs, they are replaced with that
        #: Lstr's dict.
        self.args = keywds
        our_type = type(self)

        if isinstance(self.args.get('value'), our_type):
            raise TypeError("'value' must be a regular string; not an Lstr")

        if 'subs' in keywds:
            subs = keywds.get('subs')
            subs_filtered = []
            if subs is not None:
                for key, value in keywds['subs']:
                    if isinstance(value, our_type):
                        subs_filtered.append((key, value.args))
                    else:
                        subs_filtered.append((key, value))
            self.args['subs'] = subs_filtered

        # As of protocol 31 we support compact key names ('t' instead of
        # 'translate', etc). Convert as needed.
        if 'translate' in keywds:
            keywds['t'] = keywds['translate']
            del keywds['translate']
        if 'resource' in keywds:
            keywds['r'] = keywds['resource']
            del keywds['resource']
        if 'value' in keywds:
            keywds['v'] = keywds['value']
            del keywds['value']
        if 'fallback' in keywds:
            if _babase.do_once():
                applog.error(
                    'Deprecated "fallback" arg passed to Lstr(); use '
                    'either "fallback_resource" or "fallback_value".'
                )
            keywds['f'] = keywds['fallback']
            del keywds['fallback']
        if 'fallback_resource' in keywds:
            keywds['f'] = keywds['fallback_resource']
            del keywds['fallback_resource']
        if 'subs' in keywds:
            keywds['s'] = keywds['subs']
            del keywds['subs']
        if 'fallback_value' in keywds:
            keywds['fv'] = keywds['fallback_value']
            del keywds['fallback_value']

    def evaluate(self) -> str:
        """Evaluate to a flat string in the current language.

        You should avoid doing this as much as possible and instead pass
        and store ``Lstr`` values.
        """
        return _babase.evaluate_lstr(self.as_json())

    def is_flat_value(self) -> bool:
        """Return whether this instance represents a 'flat' value.

        This is defined as a simple string value incorporating no
        translations, resources, or substitutions. In this case it may
        be reasonable to replace it with a raw string value, perform
        string manipulation on it, etc.
        """
        return bool('v' in self.args and not self.args.get('s', []))

    def as_json(self) -> str:
        """Return the json dict representation of the Lstr."""
        return json.dumps(self.args, separators=(',', ':'))

    @override
    def __repr__(self) -> str:
        return f'<babase.Lstr: {self.as_json()}>'

    @staticmethod
    def from_json(json_string: str) -> babase.Lstr:
        """Given a json string, returns a ``Lstr``.

        Does no validation.
        """
        lstr = Lstr(value='')
        lstr.args = json.loads(json_string)
        return lstr
