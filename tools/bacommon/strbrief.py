# Released under the MIT License. See LICENSE for details.
#
"""Parse the tag vocabulary in an assets_v1 ``.bstr`` authoring brief.

A ``.bstr`` ``input`` is a freeform AI-translation brief (decision D10)
carrying a small, strict inline tag vocabulary (D11) -- the only
machine-readable part. Three consumers depend on these tags
deterministically: wrapper codegen (the typed accessor signature),
generation (whether/how to produce plural forms), and validation (tag
round-trip, D12). This module extracts and validates them.

The three sigils:

* ``{name}`` -- runtime text substitution; a ``str`` wrapper param.
* ``{name#[modifier]}`` -- runtime number substitution; an ``int`` wrapper
  param and, when forms exist, the **plural pivot**. Empty modifier =
  cardinal (today); a modifier slot (e.g. ``{place#ordinal}``) is reserved
  for non-breaking future additions.
* ``{@path}`` -- a term/dictionary reference (local ``{@mystrings/apple}``
  or cross-package ``{@ref:path}``), resolved/inlined at generation time
  (D12) -- NOT a runtime param.

This is the *brief* (authoring) layer. What gets stored and evaluated at
runtime is an ICU-MessageFormat-subset message
(:mod:`bacommon.loctext`); the producer expands these tags into that form
(``{count#}`` -> ``{count, plural, one {...} other {...}}``).

Lives in shared ``bacommon`` (rather than the bamaster producer, its
original home) so authoring-side tooling can validate briefs *before*
upload -- ``assetworkspace put`` parses every local ``.bstr`` brief and
refuses the sync on parse errors, surfacing mistakes (duplicate tags,
pasted ICU, bad names) at edit time instead of minutes later inside a
server translation run. The producer imports this same module, so the
grammar cannot drift between the two.
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    from collections.abc import Iterable


class BriefTagKind(Enum):
    """Which sigil a parsed tag is."""

    TEXT = 'text'
    NUMBER = 'number'
    TERM = 'term'


@dataclass
class BriefTag:
    """One parsed inline tag from a brief."""

    kind: BriefTagKind

    #: For TEXT/NUMBER, the wrapper arg name; for TERM, the reference path.
    name: str

    #: For NUMBER tags only -- '' means cardinal (the plural pivot
    #: today), else a modifier keyword such as 'ordinal' (reserved for
    #: future use).
    modifier: str = ''


@dataclass
class BriefSignature:
    """The full tag signature extracted from a brief (in order)."""

    tags: list[BriefTag]

    @property
    def params(self) -> list[BriefTag]:
        """Wrapper params (TEXT + NUMBER tags), first-appearance order.

        Term refs are excluded -- they're resolved at generation time, not
        passed at call time.
        """
        return [t for t in self.tags if t.kind is not BriefTagKind.TERM]

    @property
    def pivot(self) -> BriefTag | None:
        """The single form-producing number tag, or None.

        The coexistence invariant guarantees at most one (enforced by
        :func:`parse_brief`).
        """
        for tag in self.tags:
            if tag.kind is BriefTagKind.NUMBER:
                return tag
        return None


# A tag is a single brace pair with no nested braces. We deliberately
# reject nested braces so a raw ICU message (``{n, plural, one {#}...}``)
# pasted into a brief fails loudly rather than parsing as garbage -- the
# brief layer uses sigils, not ICU.
_TAG_RE = re.compile(r'\{([^{}]*)\}')

#: Wrapper arg names + number modifiers are lowercase snake_case (they
#: become Python kwargs at the call site).
_IDENT_RE = re.compile(r'^[a-z][a-z0-9_]*$')

#: A ``{name}`` substitution token in generated output -- must match the
#: runtime evaluator's (``bacommon.loctext._SUB_RE``) so the round-trip
#: check sees exactly the tokens the runtime would substitute.
_SUB_TOKEN_RE = re.compile(r'\{([a-z][a-z0-9_]*)\}')

#: ICU MessageFormat argument-type keywords. Their presence means someone
#: pasted raw ICU into a brief -- worth a tailored message since the
#: brace-by-brace parse error is otherwise cryptic.
_ICU_KEYWORDS = (', plural,', ', select,', ', selectordinal,')

#: How to author a brief -- appended to "looks like ICU" errors.
_BRIEF_FORMAT_HELP = (
    'Briefs use sigils, not ICU: write `{name#}` for a count (e.g.'
    ' `{apples#}`) and the translator builds the plural forms; `{name}`'
    ' for a text substitution; `{@path}` for a term reference.'
)


def parse_brief(text: str) -> BriefSignature:
    """Extract + validate the tag signature from a brief ``input``.

    Raises :class:`~efro.error.CleanError` on raw ICU pasted into the
    brief, an empty/malformed tag, an invalid arg name or modifier, a
    duplicate arg name, or more than one number/plural pivot (the
    coexistence invariant -- a string with two independent counts should
    be split into two entries).
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
    number_count = 0

    for match in _TAG_RE.finditer(text):
        body = match.group(1).strip()
        if not body:
            raise CleanError('Empty tag `{}` in brief.')

        if body.startswith('@'):
            path = body[1:].strip()
            if not path:
                raise CleanError('Empty term reference `{@}` in brief.')
            tags.append(BriefTag(BriefTagKind.TERM, path))
            continue

        if '#' in body:
            name, _, modifier = body.partition('#')
            name = name.strip()
            modifier = modifier.strip()
            if not _IDENT_RE.match(name):
                if not name:
                    # `{# …}` -- an ICU count placeholder, not a brief tag.
                    raise CleanError(
                        f'`{{{body}}}` looks like an ICU count placeholder.'
                        f' {_BRIEF_FORMAT_HELP}'
                    )
                raise CleanError(
                    f"Invalid number-tag name '{name}' in `{{{body}}}`"
                    ' (lowercase snake_case identifier expected).'
                )
            if modifier and not _IDENT_RE.match(modifier):
                raise CleanError(
                    f"Invalid number-tag modifier '{modifier}' in"
                    f' `{{{body}}}`.'
                )
            if name in seen_names:
                raise CleanError(f"Duplicate tag name '{name}' in brief.")
            seen_names.add(name)
            number_count += 1
            tags.append(BriefTag(BriefTagKind.NUMBER, name, modifier))
            continue

        if not _IDENT_RE.match(body):
            raise CleanError(
                f"Invalid substitution name '{body}' in `{{{body}}}`"
                ' (lowercase snake_case identifier expected).'
            )
        if body in seen_names:
            raise CleanError(f"Duplicate tag name '{body}' in brief.")
        seen_names.add(body)
        tags.append(BriefTag(BriefTagKind.TEXT, body))

    if number_count > 1:
        raise CleanError(
            'A brief may contain at most one number/plural pivot `{name#}`;'
            ' split a string with two independent counts into two entries.'
        )

    return BriefSignature(tags)


def validate_round_trip(
    sig: BriefSignature,
    segments: 'Iterable[str]',
    *,
    require_count: bool,
) -> None:
    """Assert a brief's runtime tags survived correctly into generated text.

    The post-generation half of the D12 contract:

    * every ``{name}`` text-sub token must appear verbatim in each segment
      (the model must not drop or rename a runtime substitution);
    * no ``{name}`` token *other* than the declared text-subs may appear
      (the model must not invent a substitution that would fail at render);
    * with ``require_count``, each segment must contain the ``#`` count
      placeholder (every plural form renders the number);
    * no term reference ``{@...}`` may survive (those are resolved/inlined
      at generation time, never shipped as a token).

    ``segments`` is the per-locale output text(s) to check: a single output
    string for a plain/text-sub entry, or the per-plural-form texts for a
    pivot entry (so each form is verified independently). Raises
    :class:`~efro.error.CleanError` on any violation.
    """
    text_subs = [t.name for t in sig.params if t.kind is BriefTagKind.TEXT]
    allowed = set(text_subs)
    for segment in segments:
        for name in text_subs:
            token = '{' + name + '}'
            if token not in segment:
                raise CleanError(
                    f'Translation dropped the required {token} token:'
                    f' {segment!r}.'
                )
        for match in _SUB_TOKEN_RE.finditer(segment):
            if match.group(1) not in allowed:
                raise CleanError(
                    f'Translation introduced an undeclared substitution'
                    f' token `{{{match.group(1)}}}`: {segment!r}.'
                )
        if require_count and '#' not in segment:
            raise CleanError(
                f'Plural form is missing the count placeholder `#`:'
                f' {segment!r}.'
            )
        if '{@' in segment:
            raise CleanError(
                f'Unresolved term reference left in translation:'
                f' {segment!r}.'
            )
