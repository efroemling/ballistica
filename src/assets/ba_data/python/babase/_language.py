# Released under the MIT License. See LICENSE for details.
#
"""Language related functionality."""
from __future__ import annotations

import os
import json
from functools import partial
from typing import TYPE_CHECKING, overload, override

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import applog

if TYPE_CHECKING:
    from typing import Any, Sequence

    import babase


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
        self._language_target: AttrDict | None = None
        self._language_merged: AttrDict | None = None
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

        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        assert _babase.in_logic_thread()

        cfg = _babase.app.config
        cur_language = cfg.get('Lang', None)

        if ignore_redundant and language == self._language:
            return

        with open(
            os.path.join(
                _babase.app.env.data_directory,
                'ba_data',
                'data',
                'languages',
                'english.json',
            ),
            encoding='utf-8',
        ) as infile:
            lenglishvalues = json.loads(infile.read())

        # Special case - passing a complete dict for testing.
        if isinstance(language, dict):
            self._language = 'Custom'
            lmodvalues = language
            switched = False
            print_change = False
            store_to_config = False
        else:
            # Ok, we're setting a real language.

            # Store this in the config if its changing.
            if language != cur_language and store_to_config:
                # if language is None:
                #     if 'Lang' in cfg:
                #         del cfg['Lang']  # Clear it out for default.
                # else:
                cfg['Lang'] = language
                cfg.commit()
                switched = True
            else:
                switched = False

            # None implies default.
            # if language is None:
            #     language = self.default_language
            try:
                if language == 'English':
                    lmodvalues = None
                else:
                    lmodfile = os.path.join(
                        _babase.app.env.data_directory,
                        'ba_data',
                        'data',
                        'languages',
                        language.lower() + '.json',
                    )
                    with open(lmodfile, encoding='utf-8') as infile:
                        lmodvalues = json.loads(infile.read())
            except Exception:
                applog.exception("Error importing language '%s'.", language)
                _babase.screenmessage(
                    f"Error setting language to '{language}';"
                    f' see log for details.',
                    color=(1, 0, 0),
                )
                switched = False
                lmodvalues = None

            self._language = language

        # Create an attrdict of *just* our target language.
        self._language_target = AttrDict()
        langtarget = self._language_target
        assert langtarget is not None
        _add_to_attr_dict(
            langtarget, lmodvalues if lmodvalues is not None else lenglishvalues
        )

        # Create an attrdict of our target language overlaid on our base
        # (english).
        languages = [lenglishvalues]
        if lmodvalues is not None:
            languages.append(lmodvalues)
        lfull = AttrDict()
        for lmod in languages:
            _add_to_attr_dict(lfull, lmod)
        self._language_merged = lfull

        # Pass some keys/values in for low level code to use; start with
        # everything in their 'internal' section.
        internal_vals = [
            v for v in list(lfull['internal'].items()) if isinstance(v[1], str)
        ]

        # Cherry-pick various other values to include.
        # (should probably get rid of the 'internal' section
        # and do everything this way)
        for value in [
            'replayNameDefaultText',
            'replayWriteErrorText',
            'replayVersionErrorText',
            'replayReadErrorText',
        ]:
            internal_vals.append((value, lfull[value]))
        internal_vals.append(
            ('axisText', lfull['configGamepadWindow']['axisText'])
        )
        internal_vals.append(('buttonText', lfull['buttonText']))
        lmerged = self._language_merged
        assert lmerged is not None
        random_names = [
            n.strip() for n in lmerged['randomPlayerNamesText'].split(',')
        ]
        random_names = [n for n in random_names if n != '']
        _babase.set_internal_language_keys(internal_vals, random_names)
        if switched and print_change:
            assert isinstance(language, str)
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
        try:
            # If we have no language set, try and set it to english.
            # Also make a fuss because we should try to avoid this.
            if self._language_merged is None:
                try:
                    if _babase.do_once():
                        applog.warning(
                            'get_resource() called before language'
                            ' set; falling back to english.'
                        )
                    self.setlanguage(
                        'English', print_change=False, store_to_config=False
                    )
                except Exception:
                    applog.exception('Error setting fallback english language.')
                    raise

            # If they provided a fallback_resource value, try the
            # target-language-only dict first and then fall back to
            # trying the fallback_resource value in the merged dict.
            if fallback_resource is not None:
                try:
                    values = self._language_target
                    splits = resource.split('.')
                    dicts = splits[:-1]
                    key = splits[-1]
                    for dct in dicts:
                        assert values is not None
                        values = values[dct]
                    assert values is not None
                    val = values[key]
                    return val
                except Exception:
                    # FIXME: Shouldn't we try the fallback resource in
                    #  the merged dict AFTER we try the main resource in
                    #  the merged dict?
                    try:
                        values = self._language_merged
                        splits = fallback_resource.split('.')
                        dicts = splits[:-1]
                        key = splits[-1]
                        for dct in dicts:
                            assert values is not None
                            values = values[dct]
                        assert values is not None
                        val = values[key]
                        return val

                    except Exception:
                        # If we got nothing for fallback_resource,
                        # default to the normal code which checks or
                        # primary value in the merge dict; there's a
                        # chance we can get an english value for it
                        # (which we weren't looking for the first time
                        # through).
                        pass

            values = self._language_merged
            splits = resource.split('.')
            dicts = splits[:-1]
            key = splits[-1]
            for dct in dicts:
                assert values is not None
                values = values[dct]
            assert values is not None
            val = values[key]
            return val

        except Exception:
            # Ok, looks like we couldn't find our main or fallback
            # resource anywhere. Now if we've been given a fallback
            # value, return it; otherwise fail.
            from babase import _error

            if fallback_value is not None:
                return fallback_value
            raise _error.NotFoundError(
                f"Resource not found: '{resource}'"
            ) from None

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
        try:
            translated = self.get_resource('translations')[category][strval]
        except Exception as exc:
            if raise_exceptions:
                raise
            if print_errors:
                print(
                    (
                        'Translate error: category=\''
                        + category
                        + '\' name=\''
                        + strval
                        + '\' exc='
                        + str(exc)
                        + ''
                    )
                )
            translated = None
        translated_out: str
        if translated is None:
            translated_out = strval
        else:
            translated_out = translated
        assert isinstance(translated_out, str)
        return translated_out

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

    To see available resource keys, look at any of the
    ``ba_data/data/languages/*.json`` files in the game or the
    translations pages at `legacy.ballistica.net/translate
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
        # pylint: disable=too-many-branches
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
        return _babase.evaluate_lstr(self._get_json())

    def is_flat_value(self) -> bool:
        """Return whether this instance represents a 'flat' value.

        This is defined as a simple string value incorporating no
        translations, resources, or substitutions. In this case it may
        be reasonable to replace it with a raw string value, perform
        string manipulation on it, etc.
        """
        return bool('v' in self.args and not self.args.get('s', []))

    def _get_json(self) -> str:
        try:
            return json.dumps(self.args, separators=(',', ':'))
        except Exception:
            from babase import _error

            applog.exception('_get_json failed for %s.', self.args)
            return 'JSON_ERR'

    @override
    def __str__(self) -> str:
        return f'<ba.Lstr: {self._get_json()}>'

    @override
    def __repr__(self) -> str:
        return f'<ba.Lstr: {self._get_json()}>'

    @staticmethod
    def from_json(json_string: str) -> babase.Lstr:
        """Given a json string, returns a ``Lstr``.

        Does no validation.
        """
        lstr = Lstr(value='')
        lstr.args = json.loads(json_string)
        return lstr


def _add_to_attr_dict(dst: AttrDict, src: dict) -> None:
    for key, value in list(src.items()):
        if isinstance(value, dict):
            try:
                dst_dict = dst[key]
            except Exception:
                dst_dict = dst[key] = AttrDict()
            if not isinstance(dst_dict, AttrDict):
                raise RuntimeError(
                    "language key '"
                    + key
                    + "' is defined both as a dict and value"
                )
            _add_to_attr_dict(dst_dict, value)
        else:
            if not isinstance(value, (float, int, bool, str, str, type(None))):
                raise TypeError(
                    "invalid value type for res '"
                    + key
                    + "': "
                    + str(type(value))
                )
            dst[key] = value


class AttrDict(dict):
    """A dict that can be accessed with dot notation.

    (so foo.bar is equivalent to foo['bar'])
    """

    def __getattr__(self, attr: str) -> Any:
        val = self[attr]
        assert not isinstance(val, bytes)
        return val

    @override
    def __setattr__(self, attr: str, value: Any) -> None:
        raise AttributeError()
