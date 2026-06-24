# Released under the MIT License. See LICENSE for details.
#
"""Localized-text evaluation (ICU-MessageFormat subset).

A pure-Python evaluator for localized message strings carrying plural
selection and named substitutions. The string *value* delivered for a
locale is an ICU-MessageFormat-subset message; :func:`evaluate` resolves
it against a locale and caller-supplied arguments to a final ``str``.

This is the prototype of the logic the native ``Lstr2`` runtime object
will eventually implement in C++ -- keeping it here in ``bacommon`` means
the same evaluator is available to pure-Python consumers (the game
client's embedded Python, and server-side resolution in bamaster/basn)
and serves as the executable spec for the C++ port.

Supported syntax (a subset of ICU MessageFormat):

* Literal text, with ``{name}`` replaced by ``str(args['name'])``.
* ``{name, plural, [offset:N] [=N {msg}]... cat {msg}... other {msg}}`` --
  selects a plural form for the numeric argument ``name``. ``cat`` is a
  CLDR plural category (``zero``/``one``/``two``/``few``/``many``/
  ``other``); ``=N`` matches an exact value first. Within a form, ``#``
  is replaced by the number (minus any ``offset``).
* ``{name, select, key {msg}... other {msg}}`` -- selects by the string
  value of ``name`` (e.g. gender).

Forms may nest (a form's message can contain further ``{...}``
constructs). Not yet supported (prototype): ICU ``'`` quoting/escaping,
``selectordinal``, and number/date skeletons -- noted for the C++ port.
"""

from enum import Enum
from typing import TYPE_CHECKING

from bacommon.locale import Locale

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class PluralCategory(Enum):
    """A CLDR plural category."""

    ZERO = 'zero'
    ONE = 'one'
    TWO = 'two'
    FEW = 'few'
    MANY = 'many'
    OTHER = 'other'


# --- CLDR plural rules (bounded-but-real prototype set) --------------------
#
# Each rule maps an integer count to its CLDR plural category. This covers
# the major rule families and the locales exercised so far; locales not
# explicitly mapped fall back to the Germanic/Romance one-other rule (see
# _RULE_FOR_LOCALE). Expanding to the full CLDR set later is mechanical --
# add a rule function and map the locales to it.


def _rule_one_other(n: int) -> PluralCategory:
    """``one`` for 1, else ``other`` (English, German, Spanish, ...)."""
    return PluralCategory.ONE if n == 1 else PluralCategory.OTHER


def _rule_other_only(n: int) -> PluralCategory:
    """Always ``other`` (Chinese, Japanese, Korean, Thai, ...)."""
    del n  # Unused.
    return PluralCategory.OTHER


def _rule_french(n: int) -> PluralCategory:
    """``one`` for 0 and 1, else ``other`` (French, Brazilian Portuguese)."""
    return PluralCategory.ONE if n in (0, 1) else PluralCategory.OTHER


def _rule_russian(n: int) -> PluralCategory:
    """East-Slavic rule (Russian, Ukrainian, Belarussian)."""
    mod10 = n % 10
    mod100 = n % 100
    if mod10 == 1 and mod100 != 11:
        return PluralCategory.ONE
    if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
        return PluralCategory.FEW
    return PluralCategory.MANY


def _rule_polish(n: int) -> PluralCategory:
    """Polish rule (one/few/many)."""
    if n == 1:
        return PluralCategory.ONE
    mod10 = n % 10
    mod100 = n % 100
    if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
        return PluralCategory.FEW
    return PluralCategory.MANY


def _rule_czech(n: int) -> PluralCategory:
    """West-Slavic rule (Czech, Slovak): one/few/other."""
    if n == 1:
        return PluralCategory.ONE
    if 2 <= n <= 4:
        return PluralCategory.FEW
    return PluralCategory.OTHER


def _rule_arabic(n: int) -> PluralCategory:
    """Arabic rule (zero/one/two/few/many/other)."""
    mod100 = n % 100
    if n == 0:
        return PluralCategory.ZERO
    if n == 1:
        return PluralCategory.ONE
    if n == 2:
        return PluralCategory.TWO
    if 3 <= mod100 <= 10:
        return PluralCategory.FEW
    if 11 <= mod100 <= 99:
        return PluralCategory.MANY
    return PluralCategory.OTHER


# Locale -> rule. Anything absent defaults to one-other (see
# plural_category). Grouped by rule family for readability.
_RULE_FOR_LOCALE: dict[Locale, Callable[[int], PluralCategory]] = {
    # other-only (no count distinction).
    Locale.CHINESE: _rule_other_only,
    Locale.CHINESE_TRADITIONAL: _rule_other_only,
    Locale.CHINESE_SIMPLIFIED: _rule_other_only,
    Locale.JAPANESE: _rule_other_only,
    Locale.KOREAN: _rule_other_only,
    Locale.THAI: _rule_other_only,
    Locale.VIETNAMESE: _rule_other_only,
    Locale.INDONESIAN: _rule_other_only,
    Locale.MALAY: _rule_other_only,
    Locale.PERSIAN: _rule_other_only,
    # 0,1 -> one.
    Locale.FRENCH: _rule_french,
    Locale.PORTUGUESE_BRAZIL: _rule_french,
    # East-Slavic.
    Locale.RUSSIAN: _rule_russian,
    Locale.UKRAINIAN: _rule_russian,
    Locale.BELARUSSIAN: _rule_russian,
    # Polish.
    Locale.POLISH: _rule_polish,
    # West-Slavic.
    Locale.CZECH: _rule_czech,
    Locale.SLOVAK: _rule_czech,
    # Arabic.
    Locale.ARABIC: _rule_arabic,
}


def plural_category(locale: Locale, n: int) -> PluralCategory:
    """Return the CLDR plural category for a count in a locale.

    Uses the locale's resolved form so obsolete aliases (e.g. the bare
    ``SPANISH``) follow the same rule as their modern locale. Locales not
    explicitly mapped fall back to the Germanic/Romance ``one``-for-1 rule
    -- a safe, common default for the prototype's bounded ruleset.
    """
    resolved = locale.resolved.locale
    rule = _RULE_FOR_LOCALE.get(resolved, _rule_one_other)
    return rule(abs(n))


#: Canonical CLDR category order, for stable presentation.
_CATEGORY_ORDER = [
    PluralCategory.ZERO,
    PluralCategory.ONE,
    PluralCategory.TWO,
    PluralCategory.FEW,
    PluralCategory.MANY,
    PluralCategory.OTHER,
]


def required_plural_categories(locale: Locale) -> list[PluralCategory]:
    """The plural categories a ``plural`` message must cover for a locale.

    The set the locale's rule can produce over the integers, plus the
    mandatory ``other`` fallback (ICU requires it), in canonical order.
    Used to tell a translation model exactly which plural forms to emit
    for the target locale -- derived from the same rules
    :func:`plural_category` evaluates with, so producer and client agree.

    Note this is the prototype's bounded ruleset; the integer sample
    (0..200) spans every modulo cycle the current rules use.
    """
    present = {plural_category(locale, n) for n in range(201)}
    present.add(PluralCategory.OTHER)
    return [c for c in _CATEGORY_ORDER if c in present]


# --- Message-format parsing/evaluation -------------------------------------


class LocTextError(Exception):
    """A malformed localized-message string."""


def evaluate(message: str, locale: Locale, **args: object) -> str:
    """Resolve an ICU-MessageFormat-subset ``message`` to a final string.

    ``args`` supplies the named arguments referenced by ``{name}``
    substitutions and ``plural``/``select`` selectors. Plural selection
    uses ``locale``'s CLDR rule (see :func:`plural_category`).
    """
    return _eval_text(message, locale, args, pound=None)


def _find_matching_brace(s: str, open_idx: int) -> int:
    """Index of the ``}`` matching the ``{`` at ``open_idx`` (balanced)."""
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    raise LocTextError(f'Unbalanced braces in message: {s!r}.')


def _eval_text(
    text: str,
    locale: Locale,
    args: Mapping[str, object],
    pound: int | None,
) -> str:
    """Evaluate one message-text run, expanding ``{...}`` and ``#``.

    ``pound`` is the active plural number (with offset applied) so a ``#``
    inside a plural form renders the count; outside a plural it's literal.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '{':
            close = _find_matching_brace(text, i)
            out.append(_eval_arg(text[i + 1 : close], locale, args, pound))
            i = close + 1
        elif c == '#' and pound is not None:
            out.append(str(pound))
            i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def _split_top_comma(s: str, maxsplit: int) -> list[str]:
    """Split ``s`` on commas not nested inside braces (up to ``maxsplit``)."""
    parts: list[str] = []
    depth = 0
    start = 0
    for i, c in enumerate(s):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif c == ',' and depth == 0 and len(parts) < maxsplit:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _eval_arg(
    inner: str,
    locale: Locale,
    args: Mapping[str, object],
    pound: int | None,
) -> str:
    """Evaluate the contents of one ``{...}`` construct."""
    fields = _split_top_comma(inner, maxsplit=2)
    name = fields[0].strip()
    if len(fields) == 1:
        # Simple substitution.
        if name not in args:
            raise LocTextError(f'Missing argument {name!r}.')
        return str(args[name])

    kind = fields[1].strip()
    body = fields[2] if len(fields) > 2 else ''
    if kind == 'plural':
        return _eval_plural(name, body, locale, args, pound)
    if kind == 'select':
        return _eval_select(name, body, locale, args, pound)
    raise LocTextError(f'Unknown argument type {kind!r} for {name!r}.')


def _parse_forms(body: str) -> tuple[int, dict[str, str]]:
    """Parse ``[offset:N] selector {msg}...`` into (offset, {selector: msg}).

    Selectors are kept verbatim (``=N`` exact matches and CLDR category
    names); messages are the raw inner text (evaluated lazily once a form
    is selected).
    """
    offset = 0
    forms: dict[str, str] = {}
    i = 0
    n = len(body)
    while i < n:
        # Skip whitespace.
        if body[i].isspace():
            i += 1
            continue
        # Read a token up to the next '{' or whitespace.
        j = i
        while j < n and not body[j].isspace() and body[j] != '{':
            j += 1
        token = body[i:j]
        if token.startswith('offset:'):
            offset = int(token[len('offset:') :])
            i = j
            continue
        # Skip whitespace before the brace.
        while j < n and body[j].isspace():
            j += 1
        if j >= n or body[j] != '{':
            raise LocTextError(f'Expected {{...}} after {token!r} in form.')
        close = _find_matching_brace(body, j)
        forms[token] = body[j + 1 : close]
        i = close + 1
    return offset, forms


def _eval_plural(
    name: str,
    body: str,
    locale: Locale,
    args: Mapping[str, object],
    pound: int | None,
) -> str:
    """Evaluate a ``plural`` construct for numeric argument ``name``."""
    del pound  # A plural establishes its own pound value.
    if name not in args:
        raise LocTextError(f'Missing plural argument {name!r}.')
    raw = args[name]
    # ``bool`` is an ``int`` subclass but never a meaningful count.
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        raise LocTextError(
            f'Plural argument {name!r} must be a number; got {raw!r}.'
        )
    try:
        value = int(raw)
    except ValueError as exc:
        raise LocTextError(
            f'Plural argument {name!r} must be an integer; got {raw!r}.'
        ) from exc

    offset, forms = _parse_forms(body)
    # Exact ``=N`` matches win over category rules.
    exact = f'={value}'
    if exact in forms:
        return _eval_text(forms[exact], locale, args, pound=value - offset)

    category = plural_category(locale, value - offset)
    msg = forms.get(category.value)
    if msg is None:
        msg = forms.get(PluralCategory.OTHER.value)
    if msg is None:
        raise LocTextError(
            f'Plural for {name!r} has no matching form'
            f" (category {category.value!r}) and no 'other'."
        )
    return _eval_text(msg, locale, args, pound=value - offset)


def _eval_select(
    name: str,
    body: str,
    locale: Locale,
    args: Mapping[str, object],
    pound: int | None,
) -> str:
    """Evaluate a ``select`` construct keyed by the string value of ``name``."""
    if name not in args:
        raise LocTextError(f'Missing select argument {name!r}.')
    key = str(args[name])
    _offset, forms = _parse_forms(body)
    msg = forms.get(key)
    if msg is None:
        msg = forms.get('other')
    if msg is None:
        raise LocTextError(
            f'Select for {name!r} has no matching key {key!r} and no'
            " 'other'."
        )
    return _eval_text(msg, locale, args, pound=pound)
