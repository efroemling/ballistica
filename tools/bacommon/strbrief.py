# Released under the MIT License. See LICENSE for details.
#
"""Parse the tag vocabulary in an assets_v1 ``.bstr`` authoring brief.

A ``.bstr`` ``input`` is a freeform AI-translation brief (decision D10)
carrying a small, strict inline tag vocabulary (D11) -- the only
machine-readable part. Three consumers depend on these tags
deterministically: wrapper codegen (the typed accessor signature),
generation (whether/how to produce plural forms), and validation (tag
round-trip, D12). This module extracts and validates them.

The grammar is one rule::

    tag     := target [ '|' spec ]
    target  := ident | '@' refpath
    spec    := ident [ '(' kwargs ')' ]
    kwarg   := ident '=' ( int | float | true | false | ident )

Each character has exactly one job. ``@`` marks *where content comes
from* -- a term reference is resolved and inlined at generation time
(D12) rather than passed at call time, and is the only tag that is not
a wrapper param. ``:`` separates namespaces inside a reference
(``@apref:path``). ``|`` applies a *rendering spec*, the same filter
operator template languages use, so new forms cost a registry entry
rather than a new sigil:

* ``{name}`` -- runtime text substitution; a ``str`` wrapper param.
* ``{count|plural}`` -- runtime number substitution; an ``int`` wrapper
  param and the **plural pivot** (the string gains one form per CLDR
  category).
* ``{@myterms:strings/apple}`` -- a term reference. Always
  ``apref:path``; colon-less same-package refs are not supported.

Braces escape as ``{{`` and ``}}``, exactly as they do at runtime
(``bacommon.loctext``). The two layers must agree on what a brace
means, or a brief and its own translated output disagree about which
spans are tags.

Nested braces are rejected on purpose, so a raw ICU message pasted into
a brief fails loudly rather than parsing as garbage -- the brief layer
uses this grammar, not ICU.

This is the *brief* (authoring) layer. What gets stored and evaluated at
runtime is an ICU-MessageFormat-subset message
(:mod:`bacommon.loctext`); the producer expands these tags into that form
(``{count|plural}`` -> ``{count, plural, one {...} other {...}}``).

Lives in shared ``bacommon`` (rather than the bamaster producer, its
original home) so authoring-side tooling can validate briefs *before*
upload -- ``assetworkspace put`` parses every local ``.bstr`` brief and
refuses the sync on parse errors, surfacing mistakes (duplicate tags,
pasted ICU, bad names, unknown specs) at edit time instead of minutes
later inside a server translation run. The producer imports this same
module, so the grammar cannot drift between the two.
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    from typing import NoReturn
    from collections.abc import Iterable


class BriefTagKind(Enum):
    """The three things a tag can be."""

    #: A plain ``{name}`` -- text substituted at render time.
    TEXT = 'text'

    #: A ``{name|spec}`` -- a typed value rendered by its spec.
    VALUE = 'value'

    #: A ``{@path}`` term reference, inlined at generation time.
    TERM = 'term'


@dataclass(frozen=True)
class SpecDef:
    """What one registered rendering spec means.

    ``param_kind`` is the coarse call-signature category consumed by
    wrapper codegen. ``form_producing`` marks a spec that multiplies
    the *string* into per-plural-category forms rather than merely
    rendering a value into it -- the property the one-pivot rule is
    checked against. ``args`` maps each accepted keyword to its type
    (an ``int`` literal is accepted where ``float`` is declared).
    ``supported`` is False for a name that is reserved but not
    implemented; it parses, then fails with a tailored message.
    """

    param_kind: str
    form_producing: bool = False
    args: dict[str, type] = field(default_factory=dict)
    supported: bool = True


#: The spec registry -- the whole extension point. A new rendering form
#: is an entry here plus its handling in the producer/evaluator; the
#: grammar above never changes. ``ordinal`` is reserved: CLDR ordinal
#: categories are a different form set from cardinals, so it is a
#: pivot like ``plural``, not a formatter.
SPECS: dict[str, SpecDef] = {
    'plural': SpecDef(param_kind='count', form_producing=True),
    'ordinal': SpecDef(
        param_kind='count', form_producing=True, supported=False
    ),
    # A byte count rendered as human-readable size ("1.2 GB"). Takes no
    # arguments: the decimal places are adaptive (one below ten units,
    # none above), matching ``efro.util.data_size_str``, whose
    # ``compact`` flag is deliberately not carried over -- the short
    # forms exist for width-constrained debug output, not for
    # translated UI.
    'data_size': SpecDef(param_kind='bytes'),
}


@dataclass
class BriefSpec:
    """A parsed rendering spec -- the ``foo(a=1)`` in ``{x|foo(a=1)}``."""

    name: str
    args: dict[str, int | float | bool | str] = field(default_factory=dict)


@dataclass
class BriefTag:
    """One parsed inline tag from a brief."""

    kind: BriefTagKind

    #: For TEXT/VALUE, the wrapper arg name; for TERM, the reference
    #: path.
    name: str

    #: The rendering spec, or None for a plain text sub / term ref.
    spec: BriefSpec | None = None

    @property
    def param_kind(self) -> str:
        """The call-signature category for wrapper codegen."""
        if self.spec is None:
            return 'text'
        return SPECS[self.spec.name].param_kind

    @property
    def form_producing(self) -> bool:
        """Whether this tag makes the string gain plural forms."""
        return self.spec is not None and SPECS[self.spec.name].form_producing


@dataclass
class BriefSignature:
    """The full tag signature extracted from a brief (in order)."""

    tags: list[BriefTag]

    @property
    def params(self) -> list[BriefTag]:
        """Wrapper params (everything but term refs), in order.

        First-appearance order. Term refs are excluded -- they're
        resolved at generation time, not passed at call time.
        """
        return [t for t in self.tags if t.kind is not BriefTagKind.TERM]

    @property
    def pivot(self) -> BriefTag | None:
        """The single form-producing tag, or None.

        The coexistence invariant guarantees at most one (enforced by
        :func:`parse_brief`).
        """
        for tag in self.tags:
            if tag.form_producing:
                return tag
        return None

    @property
    def token_params(self) -> list[BriefTag]:
        """Params that must survive into output as a ``{name}`` token.

        Everything the runtime substitutes by name. The pivot is
        excluded: its number renders through the ICU ``#`` count
        placeholder inside each form, not through a named token.
        """
        return [t for t in self.params if not t.form_producing]


#: Scans a brief for the two brace constructs, longest-first so an
#: escaped ``{{``/``}}`` wins over a tag body -- mirroring
#: ``bacommon.loctext`` so the authoring and runtime layers agree on
#: what a brace means. A tag body is captured in group 1 and
#: deliberately admits no nested braces (see the module docstring).
_TAG_RE = re.compile(r'\{\{|\}\}|\{([^{}]*)\}')

#: Wrapper arg names, spec names, and keywords are lowercase
#: snake_case (they become Python kwargs at the call site).
_IDENT_RE = re.compile(r'^[a-z][a-z0-9_]*$')

#: A spec body: ``name`` or ``name(args)``.
_SPEC_RE = re.compile(r'^([a-z][a-z0-9_]*)(?:\((.*)\))?$')

#: Numeric spec-argument literals. Matched by pattern rather than by
#: ``int()``/``float()`` so bare words like ``inf`` and ``nan`` stay
#: enum-style identifiers instead of silently becoming floats.
_INT_RE = re.compile(r'^-?\d+$')
_FLOAT_RE = re.compile(r'^-?\d+\.\d+$')

#: A ``{name}`` substitution token in generated output -- must match the
#: runtime evaluator's so the round-trip check sees exactly the tokens
#: the runtime would substitute, escapes included.
_SUB_TOKEN_RE = re.compile(r'\{\{|\}\}|\{([a-z][a-z0-9_]*)\}')

#: An unresolved term reference in generated output. The lookbehind
#: keeps an escaped ``{{@`` (a literal brace followed by an at-sign)
#: from reading as a leaked reference.
_LEAKED_REF_RE = re.compile(r'(?<!\{)\{@')

#: ICU MessageFormat argument-type keywords. Their presence means someone
#: pasted raw ICU into a brief -- worth a tailored message since the
#: brace-by-brace parse error is otherwise cryptic.
_ICU_KEYWORDS = (', plural,', ', select,', ', selectordinal,')

#: How to author a brief -- appended to "looks like ICU" errors.
_BRIEF_FORMAT_HELP = (
    'Briefs use this grammar, not ICU: write `{name|plural}` for a count'
    ' (e.g. `{apples|plural}`) and the translator builds the plural'
    ' forms; `{name}` for a text substitution; `{@path}` for a term'
    ' reference.'
)


def parse_brief(text: str) -> BriefSignature:
    """Extract + validate the tag signature from a brief ``input``.

    Raises :class:`~efro.error.CleanError` on raw ICU pasted into the
    brief, an empty/malformed tag, an invalid arg name, an unknown or
    unsupported spec, a bad spec argument, a duplicate arg name, or more
    than one form-producing spec (the coexistence invariant -- a string
    with two independent counts should be split into two entries).
    """
    # A pasted raw ICU message is the most common mistake; catch it with a
    # message that points at the brief format rather than letting it fail
    # as a confusing tag-by-tag parse error.
    if any(kw in text.lower() for kw in _ICU_KEYWORDS):
        raise CleanError(
            f'This brief looks like raw ICU MessageFormat. {_BRIEF_FORMAT_HELP}'
        )

    tags: list[BriefTag] = []
    seen_names: set[str] = set()
    pivot_count = 0

    for match in _TAG_RE.finditer(text):
        body = match.group(1)
        if body is None:
            # An escaped `{{` or `}}` -- literal text, not a tag.
            continue
        body = body.strip()
        if not body:
            raise CleanError('Empty tag `{}` in brief.')

        tag = _parse_tag_body(body)

        if tag.kind is not BriefTagKind.TERM:
            if tag.name in seen_names:
                _raise_duplicate_tag(tag.name)
            seen_names.add(tag.name)
        if tag.form_producing:
            pivot_count += 1

        tags.append(tag)

    if pivot_count > 1:
        raise CleanError(
            'A brief may contain at most one form-producing tag'
            ' (`{name|plural}`); split a string with two independent'
            ' counts into two entries.'
        )

    return BriefSignature(tags)


def _parse_tag_body(body: str) -> BriefTag:
    """Parse one tag body (the text between the braces)."""
    target, sep, specsrc = body.partition('|')
    target = target.strip()
    specsrc = specsrc.strip()

    if '|' in specsrc:
        raise CleanError(
            f'Spec chaining is not supported in `{{{body}}}`; a tag takes'
            ' at most one `|spec`.'
        )
    if sep and not specsrc:
        raise CleanError(f'Empty spec after `|` in `{{{body}}}`.')

    if target.startswith('@'):
        path = target[1:].strip()
        if not path:
            raise CleanError('Empty term reference `{@}` in brief.')
        if specsrc:
            raise CleanError(
                f'Term references take no spec (`{{{body}}}`); no specs'
                ' are defined for them.'
            )
        return BriefTag(BriefTagKind.TERM, path)

    if not _IDENT_RE.match(target):
        if not target:
            raise CleanError(
                f'`{{{body}}}` is missing a substitution name.'
                f' {_BRIEF_FORMAT_HELP}'
            )
        if '#' in target:
            head = target.partition('#')[0].strip()
            if not head:
                # `{# …}` -- an ICU count placeholder, not a brief tag.
                raise CleanError(
                    f'`{{{body}}}` looks like an ICU count placeholder.'
                    f' {_BRIEF_FORMAT_HELP}'
                )
            # The retired pre-`|` count syntax. Worth naming explicitly
            # -- an old brief hits this rather than a generic name error.
            raise CleanError(
                f'`{{{body}}}` uses the retired `#` count syntax; write'
                f' `{{{head}|plural}}` instead.'
            )
        raise CleanError(
            f"Invalid substitution name '{target}' in `{{{body}}}`"
            ' (lowercase snake_case identifier expected).'
        )

    if not specsrc:
        return BriefTag(BriefTagKind.TEXT, target)

    return BriefTag(BriefTagKind.VALUE, target, _parse_spec(specsrc, body))


def _parse_spec(specsrc: str, body: str) -> BriefSpec:
    """Parse and validate the ``|spec`` half of a tag."""
    match = _SPEC_RE.match(specsrc)
    if match is None:
        raise CleanError(
            f"Malformed spec '{specsrc}' in `{{{body}}}`; expected"
            ' `name` or `name(arg=value, ...)`.'
        )
    name = match.group(1)
    argsrc = match.group(2)

    specdef = SPECS.get(name)
    if specdef is None:
        known = ', '.join(sorted(n for n, d in SPECS.items() if d.supported))
        raise CleanError(
            f"Unknown spec '{name}' in `{{{body}}}`. Known specs: {known}."
        )
    if not specdef.supported:
        raise CleanError(
            f"Spec '{name}' is reserved but not supported yet (`{{{body}}}`)."
        )

    args: dict[str, int | float | bool | str] = {}
    if argsrc is not None and argsrc.strip():
        for chunk in argsrc.split(','):
            key, eq, rawval = chunk.partition('=')
            key = key.strip()
            rawval = rawval.strip()
            if not eq or not _IDENT_RE.match(key):
                raise CleanError(
                    f"Malformed spec argument '{chunk.strip()}' in"
                    f' `{{{body}}}`; expected `name=value`.'
                )
            if key in args:
                raise CleanError(
                    f"Duplicate spec argument '{key}' in `{{{body}}}`."
                )
            if key not in specdef.args:
                accepted = ', '.join(sorted(specdef.args)) or '(none)'
                raise CleanError(
                    f"Spec '{name}' has no argument '{key}'"
                    f' (`{{{body}}}`). Accepted: {accepted}.'
                )
            args[key] = _parse_spec_value(rawval, key, specdef.args[key], body)

    return BriefSpec(name, args)


def _parse_spec_value(
    raw: str, key: str, wanted: type, body: str
) -> int | float | bool | str:
    """Coerce one spec argument literal to its declared type."""
    value: int | float | bool | str
    if raw in ('true', 'false'):
        value = raw == 'true'
    elif _INT_RE.match(raw):
        value = int(raw)
    elif _FLOAT_RE.match(raw):
        value = float(raw)
    elif _IDENT_RE.match(raw):
        value = raw
    else:
        raise CleanError(
            f"Invalid value '{raw}' for spec argument '{key}' in"
            f' `{{{body}}}`; expected a number, true/false, or a'
            ' lowercase identifier.'
        )

    # bool is an int subclass, so settle it before the widening rule.
    if wanted is bool:
        if not isinstance(value, bool):
            raise CleanError(
                f"Spec argument '{key}' expects true/false in"
                f" `{{{body}}}`; got '{raw}'."
            )
        return value
    if isinstance(value, bool) or not isinstance(value, wanted):
        # An int literal is accepted where a float is declared.
        if not (wanted is float and isinstance(value, int)):
            raise CleanError(
                f"Spec argument '{key}' expects {wanted.__name__} in"
                f" `{{{body}}}`; got '{raw}'."
            )
    return value


def _raise_duplicate_tag(name: str) -> 'NoReturn':
    """Report a repeated substitution tag, with the usual fix.

    Nearly always this is a tag named in prose guidance *as well as* in
    the text to be translated -- the parser can't tell those apart, so
    it reads as two declarations. Failing here is deliberate: deduping
    silently would leave the token twice in the translation prompt, and
    a model that then emitted it twice would sail through
    :func:`validate_round_trip` (which checks that declared tokens are
    present, not how often) and render the substitution twice.
    """
    raise CleanError(
        f"Duplicate tag name '{name}' in brief. Use each substitution"
        f' exactly once, in the text to be translated -- put any'
        f" guidance *about* it in the entry's docs (which also feed the"
        f' translation prompt).'
    )


def validate_round_trip(
    sig: BriefSignature,
    segments: 'Iterable[str]',
    *,
    require_count: bool,
) -> None:
    """Assert a brief's runtime tags survived correctly into generated text.

    The post-generation half of the D12 contract:

    * every ``{name}`` token param must appear verbatim in each segment
      (the model must not drop or rename a runtime substitution);
    * no ``{name}`` token *other* than those may appear (the model must
      not invent a substitution that would fail at render);
    * with ``require_count``, each segment must contain the ``#`` count
      placeholder (every plural form renders the number);
    * no term reference ``{@...}`` may survive (those are resolved/inlined
      at generation time, never shipped as a token).

    Escaped braces (``{{``/``}}``) are literal text and are skipped
    throughout, matching the runtime evaluator.

    ``segments`` is the per-locale output text(s) to check: a single output
    string for a plain/text-sub entry, or the per-plural-form texts for a
    pivot entry (so each form is verified independently). Raises
    :class:`~efro.error.CleanError` on any violation.
    """
    names = [t.name for t in sig.token_params]
    allowed = set(names)
    for segment in segments:
        for name in names:
            token = '{' + name + '}'
            if token not in segment:
                raise CleanError(
                    f'Translation dropped the required {token} token:'
                    f' {segment!r}.'
                )
        for match in _SUB_TOKEN_RE.finditer(segment):
            found = match.group(1)
            if found is None:
                # An escaped brace -- literal text, not a token.
                continue
            if found not in allowed:
                raise CleanError(
                    f'Translation introduced an undeclared substitution'
                    f' token `{{{found}}}`: {segment!r}.'
                )
        if require_count and '#' not in segment:
            raise CleanError(
                f'Plural form is missing the count placeholder `#`:'
                f' {segment!r}.'
            )
        if _LEAKED_REF_RE.search(segment):
            raise CleanError(
                f'Unresolved term reference left in translation:'
                f' {segment!r}.'
            )
