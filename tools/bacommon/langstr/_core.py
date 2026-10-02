# Released under the MIT License. See LICENSE for details.
#
"""Core of the language-string runtime model.

See ``docs/initiatives/language-string-context.md`` (ballistica-internal)
for the full design. Three pieces:

* :class:`LangStrSpec` -- a deferred, language-agnostic complex string; a
  small multitype whose forms are :class:`LangStrSpecResource` (apvernum +
  logical name + keyword substitutions), :class:`LangStrSpecValue` (a raw
  literal), and :class:`LangStrSpecResourceIndexed` (the compact
  integer-addressed projection). Substitution values are flat
  ``str``/``int`` or nested language-strings.
* :class:`LanguageStringEncodeContext` -- turns a batch of
  :class:`LangStrSpec` values into
  minimal, language-free encoded chunks plus the ``{pkg_int: apvernum}`` map.
* :class:`LanguageStringDecodeContext` -- single-locale; turns an encoded
  chunk back into a flat string via :func:`bacommon.loctext.evaluate`.

Error posture is deliberately asymmetric: encoding is the authoring side
(you control the data) so it raises :class:`LangStrError` loudly; decoding
is the consumer side (you receive data) so it is fail-visible -- it returns
an ``LANGSTR_ERROR:…`` sentinel and logs, never crashing the caller.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, assert_never, override

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from bacommon.loctext import evaluate, LocTextError
from bacommon.assetpackage import ApverNum

if TYPE_CHECKING:
    import datetime

    from bacommon.locale import Locale
    from bacommon.loctext import StringSelector

logger = logging.getLogger(__name__)

#: Cap on nested-:class:`LangStrSpec` substitution depth at decode. Wire
#: data is untrusted, so the recursive decode paths refuse trees deeper
#: than this (fail-visible) instead of recursing unboundedly.
MAX_NESTING_DEPTH = 16


@ioprepped
@dataclass
class WrapParams:
    """Constraints for splitting a text value into lines client-side.

    Mirrors the engine's simple line splitter
    (``babase.split_text_into_lines()``): text is broken only at valid
    line-break opportunities, using the fewest lines that keep every
    line within :attr:`max_chars_per_line` (when provided) while
    staying between :attr:`min_lines` and :attr:`max_lines` (``None``
    means unlimited), with line lengths balanced within that count. So
    ``max_chars_per_line`` alone gives basic wrapping and ``min_lines``
    alone gives an exact line count. Constraints are best-effort.
    Characters are counted in Latin-width units: East Asian wide
    characters (CJK, kana, Hangul, full-width forms) count as two, and
    the engine further scales the budget per locale by how wide its
    script renders (Cyrillic, Greek and Tamil run wider, Arabic and
    Hindi narrower), so a ``max_chars_per_line`` means about the same
    width in every language.

    Sizing a ``max_chars_per_line`` to a width: allow about 9.3 text
    units of width per character at text scale 1.0 (measured across
    every locale, 2026-10-01). For example, a doc-ui row footnote
    (scale 0.7) in a small-layout column (534 units of text width)
    fills well at 534 / (9.3 * 0.7), about 82. Aim a little wide
    rather than narrow: text scales down to fit its max width, so a
    slightly long line costs less than a visibly short one.

    **Default to pinning an exact line count**: set ``min_lines`` to
    the layout's designed count and leave ``max_chars_per_line``
    unset. A ``max_chars_per_line``-driven wrap yields a per-locale
    *varying* line count (translation lengths differ), which reads as
    broken in layouts designed around a specific count — and every
    legacy-converted string is such a layout, since the legacy
    pipeline hand-baked newlines at fixed counts (see D21 in the
    strings-asset-migration initiative). Reserve
    ``max_chars_per_line`` for surfaces explicitly designed to
    tolerate a variable number of lines.

    Per decision D-t these are *definition-time* presentation hints: a
    string definition carries them optionally, they ride each locale
    blob, and evaluation applies them automatically. They are
    locale-invariant, and width-driven layout consumers may ignore
    them (they are a fallback presentation default).
    """

    min_lines: Annotated[int, IOAttrs('mn', store_default=False)] = 1
    max_lines: Annotated[int | None, IOAttrs('mx', store_default=False)] = None
    max_chars_per_line: Annotated[
        int | None, IOAttrs('mc', store_default=False)
    ] = None


class LangStrError(Exception):
    """A malformed language-string or encode-context operation."""


class _DecodeFail(Exception):
    """Internal: a structural problem while decoding a chunk.

    Caught once in :meth:`LanguageStringDecodeContext.decode` and turned
    into the fail-visible ``LANGSTR_ERROR:…`` sentinel.
    """


class LangStrSpecTypeID(Enum):
    """Type IDs for the :class:`LangStrSpec` multitype's forms."""

    RESOURCE = 'r'
    VALUE = 'v'
    RESOURCE_INDEXED = 'i'
    TIME_TARGET = 'tt'


class LangStrSpec(IOMultiType[LangStrSpecTypeID]):
    """A deferred, language-agnostic complex string.

    The base of a small multitype: a language-string is a
    :class:`LangStrSpecResource` (an asset-package string addressed by
    apvernum + logical name -- the common authored form), a
    :class:`LangStrSpecValue` (a raw literal that needs no package), or a
    :class:`LangStrSpecResourceIndexed` (the compact integer-addressed
    projection of a resource, for contexts that carry a package-index
    map). All forms take keyword substitutions whose values may
    themselves be language-strings, so a ``LangStrSpec`` is a recursive
    tree; it holds tokens, not text, and only decodes to a flat string
    in some particular locale at display time. One further form,
    :class:`LangStrSpecTimeTarget`, is not a string at all but a
    substitution *value* (a moment in time) for duration params; it
    lives in this multitype because a substitution slot holds exactly
    one dataclass type.

    Wire notes: the indexed form is the multitype *default*, so it
    alone serializes without a type tag (it is the space-sensitive
    form). Clients older than ``LANGSTR_EXT_MIN_BUILD`` understand only
    tag-free resource values with flat subs; producers that know the
    client build must gate everything beyond that (nested subs and the
    value/indexed forms) on it.
    """

    @override
    @classmethod
    def get_type(cls, type_id: LangStrSpecTypeID) -> type[LangStrSpec]:
        """Return the subclass for each of our type-ids."""
        t = LangStrSpecTypeID
        if type_id is t.RESOURCE:
            return LangStrSpecResource
        if type_id is t.VALUE:
            return LangStrSpecValue
        if type_id is t.RESOURCE_INDEXED:
            return LangStrSpecResourceIndexed
        if type_id is t.TIME_TARGET:
            return LangStrSpecTimeTarget

        # Make sure we cover all cases.
        assert_never(type_id)

    @override
    @classmethod
    def get_type_id(cls) -> LangStrSpecTypeID:
        # Child classes supply this themselves.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return 't'

    @override
    @classmethod
    def get_default_type_id(cls) -> LangStrSpecTypeID | None:
        # The indexed form owns the tag-free slot: the tag would be
        # large relative to its couple of ints, and it is chosen
        # exactly when space matters. (Per dataclassio rules this
        # default is permanent once keyless data ships.)
        return LangStrSpecTypeID.RESOURCE_INDEXED


@ioprepped
@dataclass
class LangStrSpecResource(LangStrSpec):
    """An asset-package string: the common authored :class:`LangStrSpec` form.

    ``subs`` maps each substitution keyword to its value -- a flat
    ``str`` / ``int`` or a nested :class:`LangStrSpec`. A no-arg string has
    empty ``subs``. The value carries its own exact ``apvernum`` (so an
    encode context can discover the package union from the values
    themselves) and the string's logical ``name`` (mapped to its
    integer index at encode time).
    """

    apvernum: Annotated[ApverNum, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]
    subs: Annotated[
        dict[str, str | int | LangStrSpec],
        IOAttrs('s', store_default=False),
    ] = field(default_factory=dict)

    @override
    @classmethod
    def get_type_id(cls) -> LangStrSpecTypeID:
        return LangStrSpecTypeID.RESOURCE


@ioprepped
@dataclass
class LangStrSpecValue(LangStrSpec):
    """A raw literal string value needing no asset package.

    For server-generated dynamic text (player names, pre-formatted
    numbers, etc.) that rides a :class:`LangStrSpec`-shaped slot without a
    package entry. The value is locale-independent; ``subs`` are
    substituted into ``{name}`` tokens exactly like a plain resource
    value (nested language-strings allowed).

    Note that ``value`` is a *template*, not raw display text: a
    ``{name}`` token with no matching sub is a fail-visible error at
    display time. Text not authored against this contract (user input,
    error messages, anything that could contain a brace) must go
    through :meth:`literal` instead.
    """

    value: Annotated[str, IOAttrs('v')]
    subs: Annotated[
        dict[str, str | int | LangStrSpec],
        IOAttrs('s', store_default=False),
    ] = field(default_factory=dict)

    @classmethod
    def literal(cls, text: str) -> LangStrSpecValue:
        """Return a spec displaying ``text`` verbatim in every locale.

        Escapes brace characters (``{`` -> ``{{``, ``}`` -> ``}}``) so
        the substitution engine renders them literally rather than
        treating ``{...}`` runs as substitution tokens. Use this for
        any dynamic text not authored as a template -- otherwise text
        that happens to contain braces displays as a
        ``LANGSTR_ERROR:...`` sentinel.
        """
        return cls(text.replace('{', '{{').replace('}', '}}'))

    @override
    @classmethod
    def get_type_id(cls) -> LangStrSpecTypeID:
        return LangStrSpecTypeID.VALUE


@ioprepped
@dataclass
class LangStrSpecResourceIndexed(LangStrSpec):
    """The compact integer-addressed projection of a resource string.

    Usable only against a context carrying the ``{pkg_int: apvernum}``
    package-index map (and package structures for positional-sub
    ordering); see ``LanguageStringDecodeContext``. Substitutions are
    positional here (canonical param order), matching the
    :data:`EncodedLangStr` chunk model. This form is the multitype
    default, so it serializes without a type tag.
    """

    pkg: Annotated[int, IOAttrs('p')]
    index: Annotated[int, IOAttrs('n')]
    subs: Annotated[
        list[str | int | LangStrSpec],
        IOAttrs('s', store_default=False),
    ] = field(default_factory=list)

    @override
    @classmethod
    def get_type_id(cls) -> LangStrSpecTypeID:
        return LangStrSpecTypeID.RESOURCE_INDEXED


@ioprepped
@dataclass
class LangStrSpecTimeTarget(LangStrSpec):
    """A moment in time, as the value of a duration param.

    Where a plain ``int`` duration sub is a fixed signed length (the
    ``target - now`` milliseconds computed when the string was built),
    this holds the absolute moment itself, so each evaluation measures
    it against *that evaluation's* now. A string carrying one is
    therefore time-varying: a countdown ("Expires in 4m 12s") or a
    since-then readout ("Joined 3m ago") that stays correct for as long
    as it is displayed, with clients re-rendering it each time its
    visible text changes.

    Only meaningful as the substitution value of a duration-formatted
    param (``{t|duration(...)}``, in a resource's brief or a literal's
    template); that param's spec decides how it renders and in which
    direction, exactly as for a fixed length. Anywhere else -- a
    plain-text param, or evaluated on its own -- it is a decode error.

    Wrapper accessors produce one for a :class:`datetime.datetime`
    passed to a duration param without ``now``; construct directly via
    :meth:`at`.
    """

    #: The moment, as UTC epoch milliseconds.
    millis: Annotated[int, IOAttrs('m')]

    @classmethod
    def at(cls, moment: datetime.datetime) -> LangStrSpecTimeTarget:
        """Return a target for a timezone-aware datetime."""
        if moment.tzinfo is None:
            raise ValueError(
                'LangStrSpecTimeTarget requires an aware datetime.'
            )
        return cls(round(moment.timestamp() * 1000))

    @override
    @classmethod
    def get_type_id(cls) -> LangStrSpecTypeID:
        return LangStrSpecTypeID.TIME_TARGET


def time_target_offset_millis(
    target: LangStrSpecTimeTarget, now: datetime.datetime | None = None
) -> int:
    """The signed ``target - now`` length a time target measures.

    The fixed-length snapshot of a live moment, for consumers with no
    slot for one. ``now`` defaults to :func:`efro.util.utc_now`.
    """
    from efro.util import utc_now

    if now is None:
        now = utc_now()
    return target.millis - round(now.timestamp() * 1000)


#: First engine build with full current language-string support:
#: nested-:class:`LangStrSpec` substitutions, the type-tagged wire form,
#: and the value/indexed forms. Older builds understand only tag-free
#: resource values with flat subs (they tolerate an unrecognized type
#: tag on those); servers that know the client build must gate
#: everything beyond that on this floor.
LANGSTR_EXT_MIN_BUILD = 22933

#: A substitution value: a flat string/number, or a nested language-string.
type LangStrSub = str | int | LangStrSpec

#: An encoded chunk: ``[pkg_int, str_int, sub0, sub1, …]`` where each sub is
#: a flat ``str``/``int`` or a nested chunk (a list). Plain JSON -- the
#: flat-vs-nested distinction is "str/int vs list".
type EncodedLangStr = list[str | int | 'EncodedLangStr']


@dataclass(frozen=True)
class StringDef:
    """One string's language-free definition.

    ``params`` is the ordered list of ``(keyword, kind)`` where kind is
    ``'text'`` (a text sub -> ``str | LangStrSpec``) or ``'count'`` (the plural
    pivot -> ``int``); ``()`` for a no-arg string. The canonical ordering
    (sorted keyword) is what fixes the positional substitution order.

    ``docs`` (author usage docs) and ``english`` (an English preview of
    the rendered text) are optional docstring material for wrapper
    codegen only -- neither participates in the encode/decode structure.
    """

    path: str
    params: tuple[tuple[str, str], ...] = ()
    docs: str = ''
    english: str = ''


@dataclass(frozen=True)
class PackageDef:
    """Language-free definition of one asset-package-version's strings.

    The shared source the encode/decode :class:`PackageStructure` and the
    type-safe wrapper codegen both derive from (in the real system, from an
    apvernum's resolved listing; in tests, hand-built).
    """

    apvernum: ApverNum
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
            pkgdef.apvernum,
            {
                sdef.path: tuple(name for name, _kind in sdef.params)
                for sdef in pkgdef.strings
            },
        )

    @classmethod
    def from_language_values(
        cls, apvernum: ApverNum, values: dict[str, str | StringSelector]
    ) -> 'PackageStructure':
        """Derive the structure from one locale's complete value set.

        The consumer-side counterpart of :meth:`from_def`: string
        indices come from the canonical sorted-name order (the key set
        is identical across locales by construction -- see
        ``complete_locale_values``) and each string's substitution
        keywords from its own value via
        :func:`bacommon.loctext.substitution_names`. Both ends
        canonicalize param order alphabetically, so a structure derived
        here agrees with the producer's brief-derived one; producer
        tests lock that agreement.
        """
        from bacommon.loctext import substitution_names

        return cls(
            apvernum,
            {
                name: tuple(substitution_names(value))
                for name, value in values.items()
            },
        )

    def __init__(
        self, apvernum: ApverNum, strings: dict[str, tuple[str, ...]]
    ) -> None:
        #: ``strings`` maps each logical name to its substitution
        #: keywords (``()`` for a no-arg string). Order of the passed
        #: keywords is ignored: positional-substitution order is
        #: canonically alphabetical, enforced here so producer- and
        #: consumer-derived structures can't disagree on it.
        self.apvernum = apvernum
        self._names: tuple[str, ...] = tuple(sorted(strings))
        self._index: dict[str, int] = {
            name: i for i, name in enumerate(self._names)
        }
        self._params: dict[str, tuple[str, ...]] = {
            name: tuple(sorted(params)) for name, params in strings.items()
        }

    def string_count(self) -> int:
        """How many strings this package holds.

        The size of the canonical sorted name list -- all a producer
        needs to fold indices into one flat domain across a manifest.
        """
        return len(self._names)

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
    """Encodes :class:`LangStrSpec` values into minimal language-free chunks.

    Built from the batch of values to send: it computes the union of
    apvernums they reference (recursively -- nested values know their own
    apvernum) and assigns each a stable integer index. :meth:`encode` then
    emits ``[pkg_int, str_int, …subs]``; :attr:`package_index_map` is the
    only mapping the consumer needs (string indices resolve from the
    content-pinned apvernum itself).
    """

    def __init__(
        self,
        lstrs: list[LangStrSpec],
        structures: dict[ApverNum, PackageStructure],
        also: set[ApverNum] | None = None,
    ) -> None:
        self._structures = structures
        apvernums: set[ApverNum] = set()
        for lstr in lstrs:
            self._collect(lstr, apvernums)
        # ``also`` folds in packages referenced by something other than
        # strings -- asset refs, above all -- so one manifest and one
        # package-index space serves every indexed thing in a payload
        # rather than strings having a private one.
        if also:
            apvernums |= also
        # Sorted -> deterministic indices for a given apvernum set.
        self._pkg_index = {av: i for i, av in enumerate(sorted(apvernums))}

    def _collect(self, lstr: LangStrSpec, acc: set[ApverNum]) -> None:
        if isinstance(lstr, LangStrSpecResource):
            acc.add(lstr.apvernum)
            subvals = list(lstr.subs.values())
        elif isinstance(lstr, LangStrSpecValue):
            # Literals reference no package but may nest values that do.
            subvals = list(lstr.subs.values())
        elif isinstance(lstr, LangStrSpecTimeTarget):
            # A sub value, not a string; references nothing.
            return
        else:
            raise LangStrError(
                f'cannot encode an already-indexed' f' {type(lstr).__name__}.'
            )
        for val in subvals:
            if isinstance(val, LangStrSpec):
                self._collect(val, acc)

    @property
    def package_index_map(self) -> dict[int, ApverNum]:
        """The ``{pkg_int: apvernum}`` map a decoder needs."""
        return {i: av for av, i in self._pkg_index.items()}

    def encode(self, lstr: LangStrSpec) -> EncodedLangStr:
        """Encode one value (recursively) into a minimal chunk."""
        if not isinstance(lstr, LangStrSpecResource):
            raise LangStrError(
                f'only resource-form language-strings can be encoded;'
                f' got {type(lstr).__name__}.'
            )
        pkg_int = self._pkg_index.get(lstr.apvernum)
        struct = self._structures.get(lstr.apvernum)
        if pkg_int is None or struct is None:
            raise LangStrError(
                f'apvernum {lstr.apvernum!r} is not in this encode context'
            )
        try:
            str_int = struct.index_of(lstr.name)
            params = struct.params_of(lstr.name)
        except KeyError as exc:
            raise LangStrError(
                f'unknown string {lstr.name!r} in {lstr.apvernum}'
            ) from exc
        out: list[str | int | EncodedLangStr] = [pkg_int, str_int]
        for param in params:
            if param not in lstr.subs:
                raise LangStrError(
                    f'missing substitution {param!r} for {lstr.name!r}'
                )
            val = lstr.subs[param]
            if isinstance(val, LangStrSpecTimeTarget):
                # Chunks have no slot for a live moment; send the fixed
                # length it measures right now instead.
                out.append(time_target_offset_millis(val))
                continue
            out.append(
                self.encode(val) if isinstance(val, LangStrSpec) else val
            )
        return out

    def to_indexed(self, lstr: LangStrSpec) -> LangStrSpec:
        """Convert a resource/value tree to its integer-indexed form.

        Resource nodes become :class:`LangStrSpecResourceIndexed` (with
        positional subs in canonical param order); literal
        :class:`LangStrSpecValue` nodes pass through (with their nested
        subs converted). New objects are returned; the input tree is
        never mutated. Raises :class:`LangStrError` loudly for
        packages/strings unknown to this context (authoring-side
        errors) or already-indexed input.
        """
        if isinstance(lstr, LangStrSpecTimeTarget):
            # Immutable and package-free; nothing to convert.
            return lstr
        if isinstance(lstr, LangStrSpecValue):
            return LangStrSpecValue(
                lstr.value,
                {
                    key: (
                        self.to_indexed(val)
                        if isinstance(val, LangStrSpec)
                        else val
                    )
                    for key, val in lstr.subs.items()
                },
            )
        if not isinstance(lstr, LangStrSpecResource):
            raise LangStrError(f'cannot index a {type(lstr).__name__}.')
        pkg_int = self._pkg_index.get(lstr.apvernum)
        struct = self._structures.get(lstr.apvernum)
        if pkg_int is None or struct is None:
            raise LangStrError(
                f'apvernum {lstr.apvernum!r} is not in this encode context'
            )
        try:
            str_int = struct.index_of(lstr.name)
            params = struct.params_of(lstr.name)
        except KeyError as exc:
            raise LangStrError(
                f'unknown string {lstr.name!r} in {lstr.apvernum}'
            ) from exc
        subs: list[str | int | LangStrSpec] = []
        for param in params:
            if param not in lstr.subs:
                raise LangStrError(
                    f'missing substitution {param!r} for {lstr.name!r}'
                )
            val = lstr.subs[param]
            subs.append(
                self.to_indexed(val) if isinstance(val, LangStrSpec) else val
            )
        return LangStrSpecResourceIndexed(pkg=pkg_int, index=str_int, subs=subs)


class LanguageStringDecodeContext:
    """Decodes chunks into flat strings for one target locale.

    Holds the ``{pkg_int: apvernum}`` map (from the encoder), the package
    structures, and the per-apvernum string values **for a single locale**.
    :meth:`decode` resolves a chunk (recursively rendering nested values)
    via :func:`bacommon.loctext.evaluate`.
    """

    def __init__(
        self,
        package_index_map: dict[int, ApverNum],
        structures: dict[ApverNum, PackageStructure],
        language: dict[ApverNum, dict[str, str | StringSelector]],
        locale: Locale,
    ) -> None:
        #: ``language`` maps apvernum -> {string-name: value} for ``locale``.
        self._pkg_map = package_index_map
        self._structures = structures
        self._language = language
        self._locale = locale

    def decode(self, encoded: EncodedLangStr) -> str:
        """Resolve a chunk to a flat string in this context's locale.

        Fail-visible: any structural problem yields an ``LANGSTR_ERROR:…``
        sentinel (and a logged warning) rather than crashing the caller.
        """
        try:
            return self._decode(encoded)
        except _DecodeFail as exc:
            logger.warning('langstr decode: %s', exc)
            return f'LANGSTR_ERROR:{exc}'

    def _decode(self, encoded: EncodedLangStr, depth: int = 0) -> str:
        if depth > MAX_NESTING_DEPTH:
            raise _DecodeFail('max nesting depth exceeded')
        if len(encoded) < 2:
            raise _DecodeFail(f'malformed chunk {encoded!r}')
        pkg_int = encoded[0]
        str_int = encoded[1]
        if not isinstance(pkg_int, int) or not isinstance(str_int, int):
            raise _DecodeFail(f'non-int index in {encoded!r}')
        apvernum = self._pkg_map.get(pkg_int)
        if (
            apvernum is None
            or apvernum not in self._structures
            or apvernum not in self._language
        ):
            raise _DecodeFail(f'unknown package index {pkg_int}')
        struct = self._structures[apvernum]
        try:
            name = struct.name_of(str_int)
            params = struct.params_of(name)
        except IndexError, KeyError:
            raise _DecodeFail(
                f'unknown string index {str_int} in {apvernum}'
            ) from None
        values = self._language[apvernum]
        if name not in values:
            raise _DecodeFail(f'no value for {name!r} in {apvernum}')
        subs = encoded[2:]
        if len(subs) != len(params):
            raise _DecodeFail(
                f'arity mismatch for {name!r}: {len(subs)} != {len(params)}'
            )
        kwargs: dict[str, str | int] = {}
        for param, sub in zip(params, subs):
            # A nested chunk (list) renders recursively to a flat string.
            kwargs[param] = (
                self._decode(sub, depth + 1) if isinstance(sub, list) else sub
            )
        try:
            return evaluate(values[name], self._locale, **kwargs)
        except LocTextError as exc:
            raise _DecodeFail(f'eval failed for {name!r}: {exc}') from exc

    def to_resource(self, lstr: LangStrSpec, _depth: int = 0) -> LangStrSpec:
        """Convert integer-indexed nodes back to the resource form.

        The inverse of ``LanguageStringEncodeContext.to_indexed``, for
        consumers that ingest indexed wire values but hold some of them
        in the self-describing name form (e.g. deferred client effects
        that outlive their containing payload's package-index map).
        Returns new objects (resource/value nodes are rebuilt with
        converted subs); raises :class:`LangStrError` for indices
        unknown to this context.
        """
        if _depth > MAX_NESTING_DEPTH:
            raise LangStrError('max nesting depth exceeded')
        if isinstance(lstr, LangStrSpecTimeTarget):
            return lstr
        if isinstance(lstr, LangStrSpecValue):
            return LangStrSpecValue(
                lstr.value,
                {
                    key: (
                        self.to_resource(val, _depth + 1)
                        if isinstance(val, LangStrSpec)
                        else val
                    )
                    for key, val in lstr.subs.items()
                },
            )
        if isinstance(lstr, LangStrSpecResource):
            return LangStrSpecResource(
                lstr.apvernum,
                lstr.name,
                {
                    key: (
                        self.to_resource(val, _depth + 1)
                        if isinstance(val, LangStrSpec)
                        else val
                    )
                    for key, val in lstr.subs.items()
                },
            )
        if not isinstance(lstr, LangStrSpecResourceIndexed):
            raise LangStrError(f'cannot convert a {type(lstr).__name__}.')
        apvernum = self._pkg_map.get(lstr.pkg)
        if apvernum is None or apvernum not in self._structures:
            raise LangStrError(f'unknown package index {lstr.pkg}')
        struct = self._structures[apvernum]
        try:
            name = struct.name_of(lstr.index)
            params = struct.params_of(name)
        except (IndexError, KeyError) as exc:
            raise LangStrError(
                f'unknown string index {lstr.index} in {apvernum}'
            ) from exc
        if len(lstr.subs) != len(params):
            raise LangStrError(f'arity mismatch for {name!r}')
        return LangStrSpecResource(
            apvernum,
            name,
            {
                param: (
                    self.to_resource(sub, _depth + 1)
                    if isinstance(sub, LangStrSpec)
                    else sub
                )
                for param, sub in zip(params, lstr.subs)
            },
        )

    def decode_value(self, lstr: LangStrSpec) -> str:
        """Resolve any language-string form to flat text in this locale.

        The tolerant all-forms counterpart of :meth:`decode`: handles
        :class:`LangStrSpecResourceIndexed` (via this context's
        package-index map + structures), :class:`LangStrSpecValue`
        (self-contained), and plain :class:`LangStrSpecResource` (by name,
        for legacy/mixed payloads). Fail-visible like everything else
        on the decode side.
        """
        try:
            return self._decode_value(lstr, 0)
        except _DecodeFail as exc:
            logger.warning('langstr decode: %s', exc)
            return f'LANGSTR_ERROR:{exc}'

    def _decode_value(self, lstr: LangStrSpec, depth: int) -> str:
        if depth > MAX_NESTING_DEPTH:
            raise _DecodeFail('max nesting depth exceeded')
        value: str | StringSelector
        desc: str
        kwargs: dict[str, str | int] = {}
        if isinstance(lstr, LangStrSpecResourceIndexed):
            apvernum = self._pkg_map.get(lstr.pkg)
            if (
                apvernum is None
                or apvernum not in self._structures
                or apvernum not in self._language
            ):
                raise _DecodeFail(f'unknown package index {lstr.pkg}')
            struct = self._structures[apvernum]
            try:
                name = struct.name_of(lstr.index)
                params = struct.params_of(name)
            except IndexError, KeyError:
                raise _DecodeFail(
                    f'unknown string index {lstr.index} in {apvernum}'
                ) from None
            values = self._language[apvernum]
            if name not in values:
                raise _DecodeFail(f'no value for {name!r} in {apvernum}')
            if len(lstr.subs) != len(params):
                raise _DecodeFail(
                    f'arity mismatch for {name!r}:'
                    f' {len(lstr.subs)} != {len(params)}'
                )
            for param, sub in zip(params, lstr.subs):
                kwargs[param] = (
                    self._decode_value(sub, depth + 1)
                    if isinstance(sub, LangStrSpec)
                    else sub
                )
            value = values[name]
            desc = name
        elif isinstance(lstr, LangStrSpecValue):
            value = lstr.value
            desc = 'literal'
            for key, sub in lstr.subs.items():
                kwargs[key] = (
                    self._decode_value(sub, depth + 1)
                    if isinstance(sub, LangStrSpec)
                    else sub
                )
        elif isinstance(lstr, LangStrSpecResource):
            resvalues = self._language.get(lstr.apvernum)
            if resvalues is None:
                raise _DecodeFail(f'no values for package {lstr.apvernum!r}')
            resval = resvalues.get(lstr.name)
            if resval is None:
                raise _DecodeFail(
                    f'no value for {lstr.name!r} in {lstr.apvernum}'
                )
            for key, sub in lstr.subs.items():
                kwargs[key] = (
                    self._decode_value(sub, depth + 1)
                    if isinstance(sub, LangStrSpec)
                    else sub
                )
            value = resval
            desc = lstr.name
        else:
            raise _DecodeFail(f'cannot decode a {type(lstr).__name__}.')
        try:
            return evaluate(value, self._locale, **kwargs)
        except LocTextError as exc:
            raise _DecodeFail(f'eval failed for {desc!r}: {exc}') from exc


def contains_resource_form(lstr: LangStrSpec) -> bool:
    """Return whether a language-string tree contains any full
    resource-form (non-indexed) node.

    Used by consumers verifying that a wire payload claiming the
    integer-indexed form really is fully indexed (a resource-form leak
    means some producer path skipped indexing).
    """
    subvals: list[str | int | LangStrSpec]
    if isinstance(lstr, LangStrSpecResource):
        return True
    if isinstance(lstr, LangStrSpecValue):
        subvals = list(lstr.subs.values())
    elif isinstance(lstr, LangStrSpecResourceIndexed):
        subvals = list(lstr.subs)
    else:
        return False
    return any(
        isinstance(sub, LangStrSpec) and contains_resource_form(sub)
        for sub in subvals
    )


def collect_apvernums(lstr: LangStrSpec, acc: set[ApverNum]) -> None:
    """Gather every asset-package-version a language-string tree
    references into ``acc``.

    Indexed nodes resolve against an out-of-band context so they
    contribute no apvernums themselves, but their substitution values
    are still walked (a resource-form node can appear anywhere in a
    mixed tree).

    Note to implementers: keep this a module-level function; a
    self-recursive closure would create a reference cycle (function ->
    closure cell -> function) at every call site, adding cyclic-gc
    pressure the engine works hard to avoid.
    """
    subvals: list[str | int | LangStrSpec]
    if isinstance(lstr, LangStrSpecResource):
        acc.add(lstr.apvernum)
        subvals = list(lstr.subs.values())
    elif isinstance(lstr, LangStrSpecValue):
        subvals = list(lstr.subs.values())
    elif isinstance(lstr, LangStrSpecResourceIndexed):
        subvals = list(lstr.subs)
    else:
        return
    for sub in subvals:
        if isinstance(sub, LangStrSpec):
            collect_apvernums(sub, acc)
