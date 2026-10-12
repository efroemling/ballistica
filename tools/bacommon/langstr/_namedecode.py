# Released under the MIT License. See LICENSE for details.
#
"""Name-based decoding of language-strings, plus literal-template specs.

Split out of :mod:`bacommon.langstr._core` (which holds the spec forms
and the index-based encode/decode contexts) to keep both modules a
manageable size.
"""

import re
import logging
import functools
from typing import TYPE_CHECKING

from bacommon.loctext import evaluate, LocTextError
from bacommon.langstr._core import (
    MAX_NESTING_DEPTH,
    LangStrError,
    LangStrSpec,
    LangStrSpecResource,
    LangStrSpecTimeTarget,
    LangStrSpecValue,
)

if TYPE_CHECKING:
    import datetime

    from bacommon.locale import Locale
    from bacommon.loctext import StringSelector
    from bacommon.assetpackage import ApverNum

logger = logging.getLogger(__name__)


class _DecodeFail(Exception):
    """A structural problem while decoding; becomes a sentinel."""


#: A spec'd token in a literal template: ``{name|spec...}``. Escaped
#: braces match first so ``{{`` never opens a token (the same rule the
#: runtime evaluator follows).
_LITERAL_SPEC_TOKEN_RE = re.compile(
    r'\{\{|\}\}|\{([a-z][a-z0-9_]*)\|([^{}]*)\}'
)


@functools.lru_cache(maxsize=256)
def _literal_template_kinds(
    template: str,
) -> tuple[str, tuple[tuple[str, str], ...]]:
    from efro.error import CleanError
    from bacommon.strbrief import parse_tag

    kinds: dict[str, str] = {}

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name is None:
            return match.group(0)
        try:
            tag = parse_tag(f'{name}|{match.group(2)}')
        except CleanError as exc:
            raise LangStrError(
                f'bad spec in literal template {template!r}: {exc}'
            ) from exc
        if tag.form_producing:
            raise LangStrError(
                f'literal template {template!r}: form-producing specs'
                f' ({name!r}) need an authored string.'
            )
        kind = tag.display_kind
        if kinds.get(name, kind) != kind:
            raise LangStrError(
                f'literal template {template!r} gives {name!r} two specs.'
            )
        kinds[name] = kind
        return f'{{{name}}}'

    plain = _LITERAL_SPEC_TOKEN_RE.sub(_replace, template)
    return plain, tuple(kinds.items())


def literal_template_kinds(template: str) -> tuple[str, dict[str, str]]:
    """Split a literal template's spec'd tokens from its text.

    A :class:`~bacommon.langstr.LangStrSpecValue` template may mark a
    substitution with a rendering spec exactly as a brief does
    (``'Ends in {t|duration}'``), which is what lets a
    not-yet-translated literal display a formatted duration or size the
    way its eventual authored string will. Returns the template with
    each such token reduced to a plain ``{name}`` plus the
    ``{name: display-kind}`` map those specs declare (the same
    expressions a language blob carries for authored strings). Raises
    :class:`~bacommon.langstr.LangStrError` for a malformed or unknown
    spec.
    """
    if '|' not in template:
        return template, {}
    plain, kinds = _literal_template_kinds(template)
    return plain, dict(kinds)


class LanguageStringNameDecodeContext:
    """Decodes :class:`LangStrSpec` values directly, by name, for one locale.

    The name-based counterpart to
    :class:`~bacommon.langstr.LanguageStringDecodeContext`: it resolves
    an in-memory :class:`LangStrSpec` (carrying its ``apvernum``, string
    ``name``, and keyword ``subs``) straight against per-package
    per-locale values -- no integer indices, package-index-map, or
    :class:`~bacommon.langstr.PackageStructure` needed, since the subs
    are self-describing keyword->value pairs. This is the client's
    primary path: resolve the referenced packages, gather their
    per-locale values, then decode each :class:`LangStrSpec` in the
    client's locale.

    Fail-visible like
    :class:`~bacommon.langstr.LanguageStringDecodeContext` -- any
    structural problem yields an ``LANGSTR_ERROR:…`` sentinel (and a
    logged warning) rather than crashing the caller.
    """

    def __init__(
        self,
        language: dict[ApverNum, dict[str, str | StringSelector]],
        locale: Locale,
        *,
        param_kinds: dict[ApverNum, dict[str, dict[str, str]]] | None = None,
        components: (
            dict[ApverNum, dict[str, str | StringSelector]] | None
        ) = None,
        now: datetime.datetime | None = None,
    ) -> None:
        #: ``language`` maps apvernum -> {string-name: value} for ``locale``.
        self._language = language
        self._locale = locale
        #: apvernum -> {string-name: {param: kind}} for params the
        #: translated text cannot describe (a byte count renders as
        #: "1.2 GB", but the text holds only a ``{size}`` token).
        self._param_kinds = param_kinds or {}
        #: apvernum -> that package's build-embedded formatter
        #: components. Embedded rather than resolved cross-package, so
        #: rendering never depends on another package being present.
        self._components = components or {}
        #: What :class:`~bacommon.langstr.LangStrSpecTimeTarget` values
        #: measure against; ``None`` means the current time at each
        #: :meth:`decode`.
        self._now = now
        self._now_millis_cached: int | None = None
        self._merged_components_cached: (
            dict[str, str | StringSelector] | None
        ) = None

    def _merged_components(self) -> dict[str, str | StringSelector]:
        if self._merged_components_cached is None:
            merged: dict[str, str | StringSelector] = {}
            for comps in self._components.values():
                merged.update(comps)
            self._merged_components_cached = merged
        return self._merged_components_cached

    def _render_param(
        self, kindexpr: str, value: str | int, apvernum: ApverNum | None
    ) -> str:
        """Render one spec'd param value for this locale.

        ``kindexpr`` is the blob's display-kind expression -- the bare
        kind, or kind plus spec args (``'bytes(compact=true)'``); see
        :attr:`~bacommon.strbrief.BriefTag.display_kind`. Routes
        through the shared dispatch
        (:func:`~bacommon.langstr.render_display_param`) so this and
        the client wrapper runtime can't drift.
        """
        from bacommon.langstr._format import render_display_param

        # A resource renders through its own package's embedded
        # components; a literal has no package, so it takes them from
        # whichever package has them (the unit words for a locale are
        # the same in all of them).
        components = (
            self._components.get(apvernum, {})
            if apvernum is not None
            else self._merged_components()
        )
        try:
            return render_display_param(
                kindexpr, value, self._locale, components
            )
        except Exception as exc:
            raise _DecodeFail(
                f'display param render failed ({kindexpr!r}): {exc}'
            ) from exc

    def decode(self, lstr: LangStrSpec) -> str:
        """Resolve a :class:`LangStrSpec` to a flat string in this locale.

        Fail-visible: any structural problem yields an ``LANGSTR_ERROR:…``
        sentinel (and a logged warning) rather than crashing the caller.
        """
        # Every time target in one decode measures against one now.
        self._now_millis_cached = None
        try:
            return self._decode(lstr)
        except _DecodeFail as exc:
            logger.warning('langstr name-decode: %s', exc)
            return f'LANGSTR_ERROR:{exc}'

    def _now_millis(self) -> int:
        if self._now_millis_cached is None:
            from efro.util import utc_now

            now = self._now if self._now is not None else utc_now()
            self._now_millis_cached = round(now.timestamp() * 1000)
        return self._now_millis_cached

    def _decode(self, lstr: LangStrSpec, depth: int = 0) -> str:
        if depth > MAX_NESTING_DEPTH:
            raise _DecodeFail('max nesting depth exceeded')
        value: str | StringSelector
        kinds: dict[str, str] = {}
        kindsrc: ApverNum | None = None
        if isinstance(lstr, LangStrSpecValue):
            # A raw literal; the value itself is the (locale-free) text,
            # with any spec'd tokens ({t|duration}) declaring their own
            # kinds since there is no package to have declared them.
            try:
                value, kinds = literal_template_kinds(lstr.value)
            except LangStrError as exc:
                raise _DecodeFail(str(exc)) from exc
            subs = lstr.subs
            desc = 'literal'
        elif isinstance(lstr, LangStrSpecResource):
            values = self._language.get(lstr.apvernum)
            if values is None:
                raise _DecodeFail(f'no values for package {lstr.apvernum!r}')
            resval = values.get(lstr.name)
            if resval is None:
                raise _DecodeFail(
                    f'no value for {lstr.name!r} in {lstr.apvernum}'
                )
            value = resval
            subs = lstr.subs
            desc = lstr.name
            kinds = self._param_kinds.get(lstr.apvernum, {}).get(lstr.name, {})
            kindsrc = lstr.apvernum
        else:
            # The indexed form needs an index context, not this one; a
            # time target is a sub value, never a string itself.
            raise _DecodeFail(f'cannot name-decode a {type(lstr).__name__}.')
        kwargs: dict[str, str | int] = {}
        for key, sub in subs.items():
            kind = kinds.get(key)
            if isinstance(sub, LangStrSpecTimeTarget):
                # A moment renders as its offset from now through the
                # param's duration spec; it means nothing anywhere else.
                if kind is None or not kind.startswith('millis'):
                    raise _DecodeFail(
                        f'time target for {key!r} of {desc!r} needs a'
                        f' duration param.'
                    )
                kwargs[key] = self._render_param(
                    kind, sub.millis - self._now_millis(), kindsrc
                )
                continue
            if isinstance(sub, LangStrSpec):
                # A nested LangStrSpec renders recursively to a flat
                # string.
                kwargs[key] = self._decode(sub, depth + 1)
                continue
            # A spec'd param renders through locale-aware formatting
            # here, at display time -- which is what keeps the string a
            # template with a slot rather than a value baked in at
            # construction (so a live value can re-render cheaply).
            # Text passes through as-is (already-rendered text, e.g.
            # from a producer that formatted it itself).
            kwargs[key] = (
                self._render_param(kind, sub, kindsrc)
                if kind is not None and isinstance(sub, int)
                else sub
            )
        try:
            return evaluate(value, self._locale, **kwargs)
        except LocTextError as exc:
            raise _DecodeFail(f'eval failed for {desc!r}: {exc}') from exc
