# Released under the MIT License. See LICENSE for details.
#
"""Language related functionality."""
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, overload

import _ba

if TYPE_CHECKING:
    import ba
    from typing import Any, Sequence


class LanguageSubsystem:
    """Wraps up language related app functionality.

    Category: **App Classes**

    To use this class, access the single instance of it at 'ba.app.lang'.
    """

    def __init__(self) -> None:
        self.language_target: AttrDict | None = None
        self.language_merged: AttrDict | None = None
        self.default_language = self._get_default_language()

    def _can_display_language(self, language: str) -> bool:
        """Tell whether we can display a particular language.

        On some platforms we don't have unicode rendering yet
        which limits the languages we can draw.
        """

        # We don't yet support full unicode display on windows or linux :-(.
        if (
            language
            in {
                'Chinese',
                'ChineseTraditional',
                'Persian',
                'Korean',
                'Arabic',
                'Hindi',
                'Vietnamese',
                'Thai',
                'Tamil',
            }
            and not _ba.can_display_full_unicode()
        ):
            return False
        return True

    @property
    def locale(self) -> str:
        """Raw country/language code detected by the game (such as 'en_US').

        Generally for language-specific code you should look at
        ba.App.language, which is the language the game is using
        (which may differ from locale if the user sets a language, etc.)
        """
        env = _ba.env()
        assert isinstance(env['locale'], str)
        return env['locale']

    def _get_default_language(self) -> str:
        languages = {
            'de': 'German',
            'es': 'Spanish',
            'sk': 'Slovak',
            'it': 'Italian',
            'nl': 'Dutch',
            'da': 'Danish',
            'pt': 'Portuguese',
            'fr': 'French',
            'el': 'Greek',
            'ru': 'Russian',
            'pl': 'Polish',
            'sv': 'Swedish',
            'eo': 'Esperanto',
            'cs': 'Czech',
            'hr': 'Croatian',
            'hu': 'Hungarian',
            'be': 'Belarussian',
            'ro': 'Romanian',
            'ko': 'Korean',
            'fa': 'Persian',
            'ar': 'Arabic',
            'zh': 'Chinese',
            'tr': 'Turkish',
            'th': 'Thai',
            'id': 'Indonesian',
            'sr': 'Serbian',
            'uk': 'Ukrainian',
            'vi': 'Vietnamese',
            'vec': 'Venetian',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'fil': 'Filipino',
        }

        # Special case for Chinese: map specific variations to traditional.
        # (otherwise will map to 'Chinese' which is simplified)
        if self.locale in ('zh_HANT', 'zh_TW'):
            language = 'ChineseTraditional'
        else:
            language = languages.get(self.locale[:2], 'English')
        if not self._can_display_language(language):
            language = 'English'
        return language

    @property
    def language(self) -> str:
        """The name of the language the game is running in.

        This can be selected explicitly by the user or may be set
        automatically based on ba.App.locale or other factors.
        """
        assert isinstance(_ba.app.config, dict)
        return _ba.app.config.get('Lang', self.default_language)

    @property
    def available_languages(self) -> list[str]:
        """A list of all available languages.

        Note that languages that may be present in game assets but which
        are not displayable on the running version of the game are not
        included here.
        """
        langs = set()
        try:
            names = os.listdir('ba_data/data/languages')
            names = [n.replace('.json', '').capitalize() for n in names]

            # FIXME: our simple capitalization fails on multi-word names;
            # should handle this in a better way...
            for i, name in enumerate(names):
                if name == 'Chinesetraditional':
                    names[i] = 'ChineseTraditional'
        except Exception:
            from ba import _error

            _error.print_exception()
            names = []
        for name in names:
            if self._can_display_language(name):
                langs.add(name)
        return sorted(
            name for name in names if self._can_display_language(name)
        )

    def setlanguage(
        self,
        language: str | None,
        print_change: bool = True,
        store_to_config: bool = True,
    ) -> None:
        """Set the active language used for the game.

        Pass None to use OS default language.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        cfg = _ba.app.config
        cur_language = cfg.get('Lang', None)

        # Store this in the config if its changing.
        if language != cur_language and store_to_config:
            if language is None:
                if 'Lang' in cfg:
                    del cfg['Lang']  # Clear it out for default.
            else:
                cfg['Lang'] = language
            cfg.commit()
            switched = True
        else:
            switched = False

        with open(
            'ba_data/data/languages/english.json', encoding='utf-8'
        ) as infile:
            lenglishvalues = json.loads(infile.read())

        # None implies default.
        if language is None:
            language = self.default_language
        try:
            if language == 'English':
                lmodvalues = None
            else:
                lmodfile = (
                    'ba_data/data/languages/' + language.lower() + '.json'
                )
                with open(lmodfile, encoding='utf-8') as infile:
                    lmodvalues = json.loads(infile.read())
        except Exception:
            from ba import _error

            _error.print_exception('Exception importing language:', language)
            _ba.screenmessage(
                "Error setting language to '"
                + language
                + "'; see log for details",
                color=(1, 0, 0),
            )
            switched = False
            lmodvalues = None

        # Create an attrdict of *just* our target language.
        self.language_target = AttrDict()
        langtarget = self.language_target
        assert langtarget is not None
        _add_to_attr_dict(
            langtarget, lmodvalues if lmodvalues is not None else lenglishvalues
        )

        # Create an attrdict of our target language overlaid
        # on our base (english).
        languages = [lenglishvalues]
        if lmodvalues is not None:
            languages.append(lmodvalues)
        lfull = AttrDict()
        for lmod in languages:
            _add_to_attr_dict(lfull, lmod)
        self.language_merged = lfull

        # Pass some keys/values in for low level code to use;
        # start with everything in their 'internal' section.
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
        lmerged = self.language_merged
        assert lmerged is not None
        random_names = [
            n.strip() for n in lmerged['randomPlayerNamesText'].split(',')
        ]
        random_names = [n for n in random_names if n != '']
        _ba.set_internal_language_keys(internal_vals, random_names)
        if switched and print_change:
            _ba.screenmessage(
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

        DEPRECATED; use ba.Lstr functionality for these purposes.
        """
        try:
            # If we have no language set, go ahead and set it.
            if self.language_merged is None:
                language = self.language
                try:
                    self.setlanguage(
                        language, print_change=False, store_to_config=False
                    )
                except Exception:
                    from ba import _error

                    _error.print_exception(
                        'exception setting language to', language
                    )

                    # Try english as a fallback.
                    if language != 'English':
                        print('Resorting to fallback language (English)')
                        try:
                            self.setlanguage(
                                'English',
                                print_change=False,
                                store_to_config=False,
                            )
                        except Exception:
                            _error.print_exception(
                                'error setting language to english fallback'
                            )

            # If they provided a fallback_resource value, try the
            # target-language-only dict first and then fall back to trying the
            # fallback_resource value in the merged dict.
            if fallback_resource is not None:
                try:
                    values = self.language_target
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
                    # FIXME: Shouldn't we try the fallback resource in the
                    #  merged dict AFTER we try the main resource in the
                    #  merged dict?
                    try:
                        values = self.language_merged
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
                        # If we got nothing for fallback_resource, default
                        # to the normal code which checks or primary
                        # value in the merge dict; there's a chance we can
                        # get an english value for it (which we weren't
                        # looking for the first time through).
                        pass

            values = self.language_merged
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
            # Ok, looks like we couldn't find our main or fallback resource
            # anywhere. Now if we've been given a fallback value, return it;
            # otherwise fail.
            from ba import _error

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
        """Translate a value (or return the value if no translation available)

        DEPRECATED; use ba.Lstr functionality for these purposes.
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

    Category: **General Utility Classes**

    These should be used whenever possible in place of hard-coded strings
    so that in-game or UI elements show up correctly on all clients in their
    currently-active language.

    To see available resource keys, look at any of the bs_language_*.py files
    in the game or the translations pages at legacy.ballistica.net/translate.

    ##### Examples
    EXAMPLE 1: specify a string from a resource path
    >>> mynode.text = ba.Lstr(resource='audioSettingsWindow.titleText')

    EXAMPLE 2: specify a translated string via a category and english
    value; if a translated value is available, it will be used; otherwise
    the english value will be. To see available translation categories,
    look under the 'translations' resource section.
    >>> mynode.text = ba.Lstr(translate=('gameDescriptions',
    ...                                  'Defeat all enemies'))

    EXAMPLE 3: specify a raw value and some substitutions. Substitutions
    can be used with resource and translate modes as well.
    >>> mynode.text = ba.Lstr(value='${A} / ${B}',
    ...               subs=[('${A}', str(score)), ('${B}', str(total))])

    EXAMPLE 4: ba.Lstr's can be nested. This example would display the
    resource at res_a but replace ${NAME} with the value of the
    resource at res_b
    >>> mytextnode.text = ba.Lstr(
    ...     resource='res_a',
    ...     subs=[('${NAME}', ba.Lstr(resource='res_b'))])
    """

    # pylint: disable=dangerous-default-value
    # noinspection PyDefaultArgument
    @overload
    def __init__(
        self,
        *,
        resource: str,
        fallback_resource: str = '',
        fallback_value: str = '',
        subs: Sequence[tuple[str, str | Lstr]] = [],
    ) -> None:
        """Create an Lstr from a string resource."""

    # noinspection PyShadowingNames,PyDefaultArgument
    @overload
    def __init__(
        self,
        *,
        translate: tuple[str, str],
        subs: Sequence[tuple[str, str | Lstr]] = [],
    ) -> None:
        """Create an Lstr by translating a string in a category."""

    # noinspection PyDefaultArgument
    @overload
    def __init__(
        self, *, value: str, subs: Sequence[tuple[str, str | Lstr]] = []
    ) -> None:
        """Create an Lstr from a raw string value."""

    # pylint: enable=redefined-outer-name, dangerous-default-value

    def __init__(self, *args: Any, **keywds: Any) -> None:
        """Instantiate a Lstr.

        Pass a value for either 'resource', 'translate',
        or 'value'. (see Lstr help for examples).
        'subs' can be a sequence of 2-member sequences consisting of values
        and replacements.
        'fallback_resource' can be a resource key that will be used if the
        main one is not present for
        the current language in place of falling back to the english value
        ('resource' mode only).
        'fallback_value' can be a literal string that will be used if neither
        the resource nor the fallback resource is found ('resource' mode only).
        """
        # pylint: disable=too-many-branches
        if args:
            raise TypeError('Lstr accepts only keyword arguments')

        # Basically just store the exact args they passed.
        # However if they passed any Lstr values for subs,
        # replace them with that Lstr's dict.
        self.args = keywds
        our_type = type(self)

        if isinstance(self.args.get('value'), our_type):
            raise TypeError("'value' must be a regular string; not an Lstr")

        if 'subs' in self.args:
            subs_new = []
            for key, value in keywds['subs']:
                if isinstance(value, our_type):
                    subs_new.append((key, value.args))
                else:
                    subs_new.append((key, value))
            self.args['subs'] = subs_new

        # As of protocol 31 we support compact key names
        # ('t' instead of 'translate', etc). Convert as needed.
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
            from ba import _error

            _error.print_error(
                'deprecated "fallback" arg passed to Lstr(); use '
                'either "fallback_resource" or "fallback_value"',
                once=True,
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
        """Evaluate the Lstr and returns a flat string in the current language.

        You should avoid doing this as much as possible and instead pass
        and store Lstr values.
        """
        return _ba.evaluate_lstr(self._get_json())

    def is_flat_value(self) -> bool:
        """Return whether the Lstr is a 'flat' value.

        This is defined as a simple string value incorporating no translations,
        resources, or substitutions.  In this case it may be reasonable to
        replace it with a raw string value, perform string manipulation on it,
        etc.
        """
        return bool('v' in self.args and not self.args.get('s', []))

    def _get_json(self) -> str:
        try:
            return json.dumps(self.args, separators=(',', ':'))
        except Exception:
            from ba import _error

            _error.print_exception('_get_json failed for', self.args)
            return 'JSON_ERR'

    def __str__(self) -> str:
        return '<ba.Lstr: ' + self._get_json() + '>'

    def __repr__(self) -> str:
        return '<ba.Lstr: ' + self._get_json() + '>'

    @staticmethod
    def from_json(json_string: str) -> ba.Lstr:
        """Given a json string, returns a ba.Lstr. Does no data validation."""
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

    def __setattr__(self, attr: str, value: Any) -> None:
        raise Exception()
