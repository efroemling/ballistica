# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated babase (strings) asset-package wrappers.

The babase wrapper flavor exposes a package's ``.bstr`` strings as a
nested tree of call-time-resolved ``str`` accessors (asset-packages
strings phase). Unlike the scene/UI wrappers there are no loadable asset
objects here -- a leaf yields a small callable that resolves the string
against the live language table via ``_babase.get_resource`` each time
it's called, so it always reflects the current locale.

Mirrors the structure of ``bauiv1._assetwrap`` (a compact nested-dict
walked by :class:`AssetDir`), keeping per-wrapper runtime cost to one
data dict plus a handful of tiny accessor objects regardless of how many
strings the package contains (asset-packages design doc decision #28).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

#: A node in a wrapper's string tree. Each key is one path segment; a
#: ``dict`` value is a subdirectory and a ``str`` value is a leaf whose
#: string is its single-char kind code (``'n'`` for a string leaf).
type AssetNode = dict[str, str | AssetNode]


class AssetDir:
    """Dynamic accessor for one subdirectory of a strings package.

    Attribute access resolves against the wrapper's nested-dict tree: a
    subdirectory yields another :class:`AssetDir`, a leaf yields a
    callable string accessor (see :class:`_StringAsset`). All real type
    information lives in the wrapper's ``if TYPE_CHECKING:`` tree, so
    callers never type-check through this class.
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetNode, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(self, name: str) -> 'AssetDir | Callable[..., str]':
        try:
            child = self._node[name]
        except KeyError:
            raise AttributeError(name) from None
        path = f'{self._prefix}/{name}' if self._prefix else name
        if isinstance(child, dict):
            return AssetDir(self._apverid, child, path)
        return _load(path, child)


def _load(path: str, kind: str) -> 'Callable[..., str]':
    """Build a single leaf accessor by its single-char kind code."""
    if kind == 'n':
        return _StringAsset(path)
    raise ValueError(f'Invalid asset kind {kind!r} for string path {path!r}.')


class _StringAsset:
    """Callable accessor for one localized string leaf.

    Calling it resolves the string from the live language table by its
    logical path (which is its resource key) and evaluates it as an
    ICU-MessageFormat-subset message against the current locale via
    :func:`bacommon.loctext.evaluate`. So the value always tracks the
    current locale, and keyword arguments drive named substitutions and
    plural/select selection (e.g. ``apples(n=5)`` /
    ``greeting(player='Bo')``). This is the wrapper-side entry into the
    ``Lstr2`` evaluation logic prototyped in pure Python today.
    """

    __slots__ = ('_key',)

    def __init__(self, key: str) -> None:
        self._key = key

    def __call__(self, **subs: object) -> str:
        import babase
        import _babase

        from bacommon.locale import Locale
        from bacommon.loctext import evaluate, LocTextError

        value = _babase.get_resource(self._key)
        if value is None:
            # Unresolved -- the package isn't loaded / the locale blob
            # isn't registered. Fall back to the key so the miss is
            # visible rather than crashing the caller.
            return self._key
        try:
            locale = babase.app.locale.current_locale
        except RuntimeError:
            # Locale not set yet (very early boot); plural selection has
            # to assume *something* -- English is the safe default.
            locale = Locale.ENGLISH
        try:
            return evaluate(value, locale, **subs)
        except LocTextError:
            # Malformed message or missing/extra args: don't crash the
            # caller over a bad string -- surface the raw value instead.
            return value
