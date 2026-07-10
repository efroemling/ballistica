# Released under the MIT License. See LICENSE for details.
#
"""Core of the language-string runtime model.

See ``docs/initiatives/language-string-context.md`` (ballistica-internal)
for the full design. Three pieces:

* :class:`Lstr` -- a deferred, language-agnostic complex string (an apverid
  + a string name + keyword substitution values, each a flat ``str``/``int``
  or a nested :class:`Lstr`).
* :class:`LanguageStringEncodeContext` -- turns a batch of :class:`Lstr` into
  minimal, language-free encoded chunks plus the ``{pkg_int: apverid}`` map.
* :class:`LanguageStringDecodeContext` -- single-locale; turns an encoded
  chunk back into a flat string via :func:`bacommon.loctext.evaluate`.

Error posture is deliberately asymmetric: encoding is the authoring side
(you control the data) so it raises :class:`LangStrError` loudly; decoding
is the consumer side (you receive data) so it is fail-visible -- it returns
an ``LSTR_ERROR:…`` sentinel and logs, never crashing the caller.
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs
from bacommon.loctext import evaluate, LocTextError

if TYPE_CHECKING:
    from bacommon.locale import Locale
    from bacommon.loctext import StringSelector

logger = logging.getLogger(__name__)


class LangStrError(Exception):
    """A malformed language-string or encode-context operation."""


class _DecodeFail(Exception):
    """Internal: a structural problem while decoding a chunk.

    Caught once in :meth:`LanguageStringDecodeContext.decode` and turned
    into the fail-visible ``LSTR_ERROR:…`` sentinel.
    """


@ioprepped
@dataclass
class Lstr:
    """A deferred, language-agnostic complex string.

    ``subs`` maps each substitution keyword to its value -- a flat ``str`` /
    ``int`` or a nested :class:`Lstr`. A no-arg string has empty ``subs``.
    The value carries its own exact ``apverid`` (so an encode context can
    discover the package union from the values themselves) and the string's
    logical ``name`` (mapped to its integer index at encode time).

    This is ``@ioprepped`` so it can be sent directly on the wire (the
    name-based docui-v2 form). Flat ``str``/``int`` subs serialize directly;
    nested-:class:`Lstr` subs are exercised by the in-memory encode /
    name-decode paths but are not yet directly JSON-serializable here (they
    graduate with the integer-indexed :data:`EncodedLstr` form).
    """

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]
    subs: Annotated[dict, IOAttrs('s', store_default=False)] = field(
        default_factory=dict
    )


#: A substitution value: a flat string/number, or a nested language-string.
type LstrSub = str | int | Lstr

#: An encoded chunk: ``[pkg_int, str_int, sub0, sub1, …]`` where each sub is
#: a flat ``str``/``int`` or a nested chunk (a list). Plain JSON -- the
#: flat-vs-nested distinction is "str/int vs list".
type EncodedLstr = list[str | int | 'EncodedLstr']


@dataclass(frozen=True)
class StringDef:
    """One string's language-free definition.

    ``params`` is the ordered list of ``(keyword, kind)`` where kind is
    ``'text'`` (a text sub -> ``str | Lstr``) or ``'count'`` (the plural
    pivot -> ``int``); ``()`` for a no-arg string. The canonical ordering
    (sorted keyword) is what fixes the positional substitution order.
    """

    path: str
    params: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PackageDef:
    """Language-free definition of one asset-package-version's strings.

    The shared source the encode/decode :class:`PackageStructure` and the
    type-safe wrapper codegen both derive from (in the real system, from an
    apverid's resolved listing; in tests, hand-built).
    """

    apverid: str
    strings: tuple[StringDef, ...]


class PackageStructure:
    """Language-free structure of one asset-package-version.

    Maps string names <-> integer indices (assigned in canonical
    sorted-name order so both ends agree without shipping the mapping) and
    holds each string's ordered substitution-keyword list. Carries no
    translations -- encoding needs only this.
    """

    @classmethod
    def from_def(cls, pkgdef: PackageDef) -> 'PackageStructure':
        """Build the encode/decode structure from a package definition."""
        return cls(
            pkgdef.apverid,
            {
                sdef.path: tuple(name for name, _kind in sdef.params)
                for sdef in pkgdef.strings
            },
        )

    def __init__(
        self, apverid: str, strings: dict[str, tuple[str, ...]]
    ) -> None:
        #: ``strings`` maps each logical name to its ordered substitution
        #: keywords (``()`` for a no-arg string).
        self.apverid = apverid
        self._names: tuple[str, ...] = tuple(sorted(strings))
        self._index: dict[str, int] = {
            name: i for i, name in enumerate(self._names)
        }
        self._params: dict[str, tuple[str, ...]] = dict(strings)

    def index_of(self, name: str) -> int:
        """Return the integer index for a string name."""
        return self._index[name]

    def name_of(self, index: int) -> str:
        """Return the string name for an integer index."""
        return self._names[index]

    def params_of(self, name: str) -> tuple[str, ...]:
        """Return the ordered substitution keywords for a string name."""
        return self._params[name]


class LanguageStringEncodeContext:
    """Encodes :class:`Lstr` values into minimal language-free chunks.

    Built from the batch of values to send: it computes the union of
    apverids they reference (recursively -- nested values know their own
    apverid) and assigns each a stable integer index. :meth:`encode` then
    emits ``[pkg_int, str_int, …subs]``; :attr:`package_index_map` is the
    only mapping the consumer needs (string indices resolve from the
    content-pinned apverid itself).
    """

    def __init__(
        self,
        lstrs: list[Lstr],
        structures: dict[str, PackageStructure],
    ) -> None:
        self._structures = structures
        apverids: set[str] = set()
        for lstr in lstrs:
            self._collect(lstr, apverids)
        # Sorted -> deterministic indices for a given apverid set.
        self._pkg_index = {av: i for i, av in enumerate(sorted(apverids))}

    def _collect(self, lstr: Lstr, acc: set[str]) -> None:
        acc.add(lstr.apverid)
        for val in lstr.subs.values():
            if isinstance(val, Lstr):
                self._collect(val, acc)

    @property
    def package_index_map(self) -> dict[int, str]:
        """The ``{pkg_int: apverid}`` map a decoder needs."""
        return {i: av for av, i in self._pkg_index.items()}

    def encode(self, lstr: Lstr) -> EncodedLstr:
        """Encode one value (recursively) into a minimal chunk."""
        pkg_int = self._pkg_index.get(lstr.apverid)
        struct = self._structures.get(lstr.apverid)
        if pkg_int is None or struct is None:
            raise LangStrError(
                f'apverid {lstr.apverid!r} is not in this encode context'
            )
        try:
            str_int = struct.index_of(lstr.name)
            params = struct.params_of(lstr.name)
        except KeyError as exc:
            raise LangStrError(
                f'unknown string {lstr.name!r} in {lstr.apverid}'
            ) from exc
        out: list[str | int | EncodedLstr] = [pkg_int, str_int]
        for param in params:
            if param not in lstr.subs:
                raise LangStrError(
                    f'missing substitution {param!r} for {lstr.name!r}'
                )
            val = lstr.subs[param]
            out.append(self.encode(val) if isinstance(val, Lstr) else val)
        return out


class LanguageStringDecodeContext:
    """Decodes chunks into flat strings for one target locale.

    Holds the ``{pkg_int: apverid}`` map (from the encoder), the package
    structures, and the per-apverid string values **for a single locale**.
    :meth:`decode` resolves a chunk (recursively rendering nested values)
    via :func:`bacommon.loctext.evaluate`.
    """

    def __init__(
        self,
        package_index_map: dict[int, str],
        structures: dict[str, PackageStructure],
        language: dict[str, dict[str, str | StringSelector]],
        locale: Locale,
    ) -> None:
        #: ``language`` maps apverid -> {string-name: value} for ``locale``.
        self._pkg_map = package_index_map
        self._structures = structures
        self._language = language
        self._locale = locale

    def decode(self, encoded: EncodedLstr) -> str:
        """Resolve a chunk to a flat string in this context's locale.

        Fail-visible: any structural problem yields an ``LSTR_ERROR:…``
        sentinel (and a logged warning) rather than crashing the caller.
        """
        try:
            return self._decode(encoded)
        except _DecodeFail as exc:
            logger.warning('langstr decode: %s', exc)
            return f'LSTR_ERROR:{exc}'

    def _decode(self, encoded: EncodedLstr) -> str:
        if len(encoded) < 2:
            raise _DecodeFail(f'malformed chunk {encoded!r}')
        pkg_int = encoded[0]
        str_int = encoded[1]
        if not isinstance(pkg_int, int) or not isinstance(str_int, int):
            raise _DecodeFail(f'non-int index in {encoded!r}')
        apverid = self._pkg_map.get(pkg_int)
        if (
            apverid is None
            or apverid not in self._structures
            or apverid not in self._language
        ):
            raise _DecodeFail(f'unknown package index {pkg_int}')
        struct = self._structures[apverid]
        try:
            name = struct.name_of(str_int)
            params = struct.params_of(name)
        except IndexError, KeyError:
            raise _DecodeFail(
                f'unknown string index {str_int} in {apverid}'
            ) from None
        values = self._language[apverid]
        if name not in values:
            raise _DecodeFail(f'no value for {name!r} in {apverid}')
        subs = encoded[2:]
        if len(subs) != len(params):
            raise _DecodeFail(
                f'arity mismatch for {name!r}: {len(subs)} != {len(params)}'
            )
        kwargs: dict[str, str | int] = {}
        for param, sub in zip(params, subs):
            # A nested chunk (list) renders recursively to a flat string.
            kwargs[param] = self.decode(sub) if isinstance(sub, list) else sub
        try:
            return evaluate(values[name], self._locale, **kwargs)
        except LocTextError as exc:
            raise _DecodeFail(f'eval failed for {name!r}: {exc}') from exc


class LanguageStringNameDecodeContext:
    """Decodes :class:`Lstr` values directly, by name, for one locale.

    The name-based counterpart to :class:`LanguageStringDecodeContext`: it
    resolves an in-memory :class:`Lstr` (carrying its ``apverid``, string
    ``name``, and keyword ``subs``) straight against per-apverid per-locale
    values -- no integer indices, package-index-map, or
    :class:`PackageStructure` needed, since the subs are self-describing
    keyword->value pairs. This is the client's primary path: resolve the
    referenced packages, gather their per-locale values, then decode each
    :class:`Lstr` in the client's locale.

    Fail-visible like :class:`LanguageStringDecodeContext` -- any structural
    problem yields an ``LSTR_ERROR:…`` sentinel (and a logged warning) rather
    than crashing the caller.
    """

    def __init__(
        self,
        language: dict[str, dict[str, str | StringSelector]],
        locale: Locale,
    ) -> None:
        #: ``language`` maps apverid -> {string-name: value} for ``locale``.
        self._language = language
        self._locale = locale

    def decode(self, lstr: Lstr) -> str:
        """Resolve an :class:`Lstr` to a flat string in this context's locale.

        Fail-visible: any structural problem yields an ``LSTR_ERROR:…``
        sentinel (and a logged warning) rather than crashing the caller.
        """
        try:
            return self._decode(lstr)
        except _DecodeFail as exc:
            logger.warning('langstr name-decode: %s', exc)
            return f'LSTR_ERROR:{exc}'

    def _decode(self, lstr: Lstr) -> str:
        values = self._language.get(lstr.apverid)
        if values is None:
            raise _DecodeFail(f'no values for package {lstr.apverid!r}')
        value = values.get(lstr.name)
        if value is None:
            raise _DecodeFail(f'no value for {lstr.name!r} in {lstr.apverid}')
        kwargs: dict[str, str | int] = {}
        for key, sub in lstr.subs.items():
            # A nested Lstr renders recursively to a flat string.
            kwargs[key] = self._decode(sub) if isinstance(sub, Lstr) else sub
        try:
            return evaluate(value, self._locale, **kwargs)
        except LocTextError as exc:
            raise _DecodeFail(f'eval failed for {lstr.name!r}: {exc}') from exc
